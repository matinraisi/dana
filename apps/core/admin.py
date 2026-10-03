from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline
from django.db.models import Sum
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.html import format_html
import jdatetime

from .models import BusinessUnit, User, Partner, PartnerRevenue, Project, Task, ProjectFile
from apps.crm.models import Lead
from apps.accounting.models import Invoice
from django.db.models import Sum, Avg
# --- Dashboard Callback ---
def dashboard_callback(request, context):
    projects = Project.objects.all()
    total_revenue = Invoice.objects.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    projects_count = projects.count()
    avg_profit_val = sum(p.net_profit for p in projects) / projects_count if projects_count > 0 else 0

    context.update({
            "new_leads_count": Lead.objects.filter(status='NEW').count(),
            "total_revenue": Invoice.objects.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            "avg_profit": PartnerRevenue.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
            "active_projects_count": Lead.objects.exclude(status__in=['REJECTED', 'DONE']).count(),
            "total_projects": Invoice.objects.count(),
            
            # تعریف دیتای نمودار (نمونه)
            "sample_chart": {
                "labels": ["فروردین", "اردیبهشت", "خرداد", "تیر"],
                "datasets": [{
                    "label": "جریان نقدینگی",
                    "data": [12, 19, 3, 5],
                    "backgroundColor": "#8b5cf6",
                }]
            },
        })
    return context

# --- Admin Registrations ---

@admin.register(BusinessUnit)
class BusinessUnitAdmin(ModelAdmin):
    # فیلدهای slug و created_at چون در مدل نبودند حذف شدند
    list_display = ["name", "primary_color"]

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ["username", "email", "get_businesses", "is_staff"]
    fieldsets = (
        ("اطلاعات ورود", {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "email", "phone_number", "profile_image")}),
        ("دسترسی‌های تجاری", {"fields": ("businesses",)}),
        ("وضعیت دسترسی", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    def get_businesses(self, obj):
        return ", ".join([b.name for b in obj.businesses.all()])
    get_businesses.short_description = "واحدهای تجاری"

@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    list_display = ["user", "share_percentage"]

@admin.register(PartnerRevenue)
class PartnerRevenueAdmin(ModelAdmin):
    list_display = ["partner", "project", "amount"]

class ProjectFileInline(TabularInline):
    model = ProjectFile
    extra = 1

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # لیست کامل ستون‌ها شامل تاریخ شمسی و مبالغ فرمت شده
    list_display = [
        "title", 
        "business_unit", 
        "status", 
        "get_start_date_jalali", 
        "get_deadline_jalali", 
        "budget_display", 
        "net_profit_display",
        "profit_action"
    ]    
    list_filter = (
        ('start_date', admin.DateFieldListFilter),
        'status',
        'business_unit',
    )
    inlines = [ProjectFileInline]
    
    class Media:
        js = (
            "https://unpkg.com/@persian-tools/persian-datepicker/dist/persian-datepicker.min.js",
            "admin/js/custom_jalali.js",
        )
        css = {
            "all": ("https://unpkg.com/@persian-tools/persian-datepicker/dist/persian-datepicker.min.css",)
        }
    
    def get_unfold_template_variables(self, request, obj=None):
        variables = super().get_unfold_template_variables(request, obj)
        if obj and obj.business_unit:
            variables.update({
                "unfold_primary_color": obj.business_unit.primary_color,
            })
        return variables

    @admin.display(description="تاریخ شروع")
    def get_start_date_jalali(self, obj):
        if obj.start_date:
            return jdatetime.date.fromgregorian(date=obj.start_date).strftime("%Y/%m/%d")
        return "-"

    @admin.display(description="مهلت نهایی")
    def get_deadline_jalali(self, obj):
        if obj.deadline:
            return jdatetime.date.fromgregorian(date=obj.deadline).strftime("%Y/%m/%d")
        return "-"
    
    @admin.display(description="بودجه کل")
    def budget_display(self, obj):
        return f"{intcomma(obj.total_budget)} ریال"

    @admin.display(description="سود خالص")
    def net_profit_display(self, obj):
        profit = obj.net_profit
        color = "emerald" if profit >= 0 else "red"
        return format_html(
            '<span class="font-bold text-{}-500">{} ریال</span>',
            color,
            intcomma(profit)
        )

    @admin.display(description="وضعیت توزیع")
    def profit_action(self, obj):
        if obj.status == 'COMPLETED':
            return "آماده توزیع"
        return "در جریان"

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ["title", "project", "assigned_to", "priority_display", "is_completed", "due_date"]
    list_editable = ["is_completed"]
    list_filter = ["priority", "is_completed", "project"]

    @admin.display(description="اولویت")
    def priority_display(self, obj):
        colors = {'HIGH': '#ef4444', 'MEDIUM': '#f59e0b', 'LOW': '#3b82f6'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.priority, 'white'), obj.get_priority_display())
    
    
    
@admin.register(ProjectFile)
class ProjectFileAdmin(ModelAdmin):
    list_display = ["title", "project", "uploaded_at"]
    list_filter = ["project"]
    search_fields = ["title"]