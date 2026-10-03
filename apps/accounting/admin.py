from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django.db.models import Sum
from .models import Transaction, Invoice, InvoiceItem
from .views import render_invoice_pdf
from django.utils.html import format_html
from django.urls import path
class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ["description", "quantity", "unit_price"]

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ["title", "business_unit", "type", "amount", "status", "created_at"]
    list_filter = ["type", "status", "business_unit"]
    search_fields = ["title"]
    actions = ["make_paid"]

    @admin.action(description="تغییر وضعیت به پرداخت شده")
    def make_paid(self, request, queryset):
        queryset.update(status='PAID')

    def changelist_view(self, request, extra_context=None):
        total_income = Transaction.objects.filter(type='INCOME', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = Transaction.objects.filter(type='EXPENSE', status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
        
        extra_context = extra_context or {}
        extra_context['dashboard_stats'] = [
            {"title": "مجموع درآمد تایید شده", "value": f"{total_income:,} تومان"},
            {"title": "مجموع هزینه‌ها", "value": f"{total_expense:,} تومان"},
        ]
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('id', 'client', 'total_amount', 'status', 'pdf_actions')   
    list_filter = ["is_paid", "status", "business_unit"]
    search_fields = ["invoice_number", "client__name"]
    inlines = [InvoiceItemInline]
    def pdf_actions(self, obj):
            # آدرس URL را بر اساس نامی که در get_urls تعریف می‌کنیم می‌سازیم
            return format_html(
                '<a class="button" style="background-color: #79aec8; color: white; padding: 5px 10px; border-radius: 4px;" '
                'href="{}">📥 دانلود PDF</a>',
                f'/admin/accounting/invoice/{obj.id}/pdf/'
            )
        
        # این خط باید دقیقاً اینجا باشد (هم‌سطح با def)
    pdf_actions.short_description = "عملیات"

        # اضافه کردن URL سفارشی به ادمین جنگو
    def get_urls(self):
            urls = super().get_urls()
            custom_urls = [
                path(
                    '<int:invoice_id>/pdf/',
                    self.admin_site.admin_view(render_invoice_pdf),
                    name='invoice-pdf',
                ),
            ]
            return custom_urls + urls
        
    # آپدیت خودکار مبلغ کل بعد از ذخیره آیتم‌ها
    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        form.instance.update_total()
        return instances