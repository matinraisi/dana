import re
import secrets
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import Customer, InstallRecord, License, ProvisioningRequest
from .services import notify_admins_of_provisioning_request


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_IRANIAN_PHONE = re.compile(r"^09\d{9}$")


def normalize_iranian_phone(value: str) -> str:
    value = (value or "").translate(_PERSIAN_DIGITS)
    value = re.sub(r"[\s\-()]", "", value)
    if value.startswith("0098"):
        value = "0" + value[4:]
    elif value.startswith("+98"):
        value = "0" + value[3:]
    elif value.startswith("98") and len(value) == 12:
        value = "0" + value[2:]
    return value


class ProvisioningRequestCreateView(View):
    template_name = "control_center/request_form.html"
    duplicate_window = timedelta(minutes=5)

    def get(self, request):
        return render(request, self.template_name, {"product_choices": ProvisioningRequest.PRODUCT_CHOICES})

    def post(self, request):
        data = {
            "organization_name": request.POST.get("organization_name", "").strip(),
            "contact_name": request.POST.get("contact_name", "").strip(),
            "phone_number": normalize_iranian_phone(request.POST.get("phone_number", "")),
            "email": request.POST.get("email", "").strip(),
            "requested_product": request.POST.get("requested_product", ""),
            "message": request.POST.get("message", "").strip(),
        }
        valid_products = {value for value, _ in ProvisioningRequest.PRODUCT_CHOICES}
        if not all((data["organization_name"], data["contact_name"], data["phone_number"])):
            messages.error(request, "نام مجموعه، نام مسئول و شماره تماس الزامی هستند.")
        elif not _IRANIAN_PHONE.fullmatch(data["phone_number"]):
            messages.error(request, "شماره تماس را به صورت ۰۹xxxxxxxxx وارد کنید.")
        elif data["requested_product"] not in valid_products:
            messages.error(request, "محصول درخواستی معتبر نیست.")
        elif ProvisioningRequest.objects.filter(
            phone_number=data["phone_number"],
            created_at__gte=timezone.now() - self.duplicate_window,
        ).exists():
            messages.info(request, "درخواست شما ثبت شده است؛ به‌زودی با شما تماس می‌گیریم.")
            return redirect("control_center:request_create")
        else:
            provisioning_request = ProvisioningRequest.objects.create(**data)
            if notify_admins_of_provisioning_request(provisioning_request):
                provisioning_request.notified_at = timezone.now()
                provisioning_request.save(update_fields=["notified_at"])
            messages.success(request, "درخواست شما ثبت شد. به‌زودی با شما تماس می‌گیریم.")
            return redirect("control_center:request_create")

        return render(request, self.template_name, {
            "product_choices": ProvisioningRequest.PRODUCT_CHOICES,
            "post": data,
        })


class ControlAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "/admin/login/"
    raise_exception = True

    def test_func(self):
        return self.request.user.is_superuser


class ProvisioningRequestListView(ControlAdminRequiredMixin, View):
    template_name = "control_center/request_list.html"

    def get(self, request):
        query = request.GET.get("q", "").strip()
        status = request.GET.get("status", "")
        requests_qs = ProvisioningRequest.objects.all()
        if query:
            requests_qs = requests_qs.filter(
                Q(organization_name__icontains=query)
                | Q(contact_name__icontains=query)
                | Q(phone_number__icontains=query)
            )
        if status:
            requests_qs = requests_qs.filter(status=status)
        page_obj = Paginator(requests_qs, 25).get_page(request.GET.get("page", 1))
        return render(request, self.template_name, {
            "page_obj": page_obj,
            "statuses": ProvisioningRequest.STATUS_CHOICES,
            "active_status": status,
            "query": query,
            "nav": "requests",
        })


class ProvisioningRequestUpdateView(ControlAdminRequiredMixin, View):
    def post(self, request, pk):
        provisioning_request = get_object_or_404(ProvisioningRequest, pk=pk)
        status = request.POST.get("status")
        valid_statuses = {value for value, _ in ProvisioningRequest.STATUS_CHOICES}
        if status in valid_statuses:
            provisioning_request.status = status
        provisioning_request.internal_note = request.POST.get("internal_note", "").strip()
        provisioning_request.save(update_fields=["status", "internal_note", "updated_at"])

        if request.POST.get("convert_customer") == "1":
            customer, created = Customer.objects.get_or_create(
                phone_number=provisioning_request.phone_number,
                organization_name=provisioning_request.organization_name,
                defaults={
                    "product_profile": provisioning_request.requested_product,
                    "contact_name": provisioning_request.contact_name,
                    "email": provisioning_request.email,
                    "source_request": provisioning_request,
                    "status": Customer.STATUS_TRIAL,
                },
            )
            if created:
                messages.success(request, f"مشتری «{customer.organization_name}» ساخته شد.")
            else:
                messages.info(request, "مشتری از قبل وجود داشت.")
            return redirect("control_center:customer_list")

        messages.success(request, "درخواست به‌روزرسانی شد.")
        return redirect("control_center:request_list")


class CustomerListView(ControlAdminRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        status = request.GET.get("status", "")
        qs = Customer.objects.all()
        if query:
            qs = qs.filter(
                Q(organization_name__icontains=query)
                | Q(contact_name__icontains=query)
                | Q(phone_number__icontains=query)
            )
        if status:
            qs = qs.filter(status=status)
        return render(request, "control_center/customer_list.html", {
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "statuses": Customer.STATUS_CHOICES,
            "active_status": status,
            "query": query,
            "nav": "customers",
        })


class CustomerFormView(ControlAdminRequiredMixin, View):
    def get(self, request, pk=None):
        obj = get_object_or_404(Customer, pk=pk) if pk else Customer(status=Customer.STATUS_TRIAL)
        return render(request, "control_center/customer_form.html", {
            "obj": obj,
            "title": "ویرایش مشتری" if pk else "مشتری جدید",
            "product_choices": Customer.PRODUCT_CHOICES,
            "statuses": Customer.STATUS_CHOICES,
            "nav": "customers",
        })

    def post(self, request, pk=None):
        obj = get_object_or_404(Customer, pk=pk) if pk else Customer()
        obj.organization_name = request.POST.get("organization_name", "").strip()
        obj.product_profile = request.POST.get("product_profile", Customer.PRODUCT_ACADEMY)
        obj.contact_name = request.POST.get("contact_name", "").strip()
        obj.phone_number = normalize_iranian_phone(request.POST.get("phone_number", ""))
        obj.email = request.POST.get("email", "").strip()
        obj.status = request.POST.get("status", Customer.STATUS_TRIAL)
        obj.notes = request.POST.get("notes", "").strip()
        if not obj.organization_name or not obj.contact_name or not obj.phone_number:
            messages.error(request, "فیلدهای الزامی را کامل کنید.")
            return redirect(request.path)
        obj.save()
        messages.success(request, "مشتری ذخیره شد.")
        return redirect("control_center:customer_list")


class LicenseListView(ControlAdminRequiredMixin, View):
    def get(self, request):
        qs = License.objects.select_related("customer")
        return render(request, "control_center/license_list.html", {
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "nav": "licenses",
        })


class LicenseFormView(ControlAdminRequiredMixin, View):
    def get(self, request, pk=None):
        obj = get_object_or_404(License, pk=pk) if pk else License(status=License.STATUS_ACTIVE)
        return render(request, "control_center/license_form.html", {
            "obj": obj,
            "title": "ویرایش لایسنس" if pk else "لایسنس جدید",
            "customers": Customer.objects.order_by("organization_name"),
            "statuses": License.STATUS_CHOICES,
            "generated_key": f"DANA-{uuid.uuid4().hex[:12].upper()}",
            "nav": "licenses",
        })

    def post(self, request, pk=None):
        obj = get_object_or_404(License, pk=pk) if pk else License()
        obj.customer_id = request.POST.get("customer_id")
        obj.license_key = request.POST.get("license_key", "").strip() or f"DANA-{secrets.token_hex(6).upper()}"
        obj.plan_name = request.POST.get("plan_name", "standard").strip() or "standard"
        obj.status = request.POST.get("status", License.STATUS_ACTIVE)
        obj.starts_at = request.POST.get("starts_at") or timezone.localdate()
        ends = request.POST.get("ends_at") or None
        obj.ends_at = ends or None
        obj.website_enabled = request.POST.get("website_enabled") == "on"
        obj.notes = request.POST.get("notes", "").strip()
        obj.save()
        messages.success(request, "لایسنس ذخیره شد.")
        return redirect("control_center:license_list")


class InstallListView(ControlAdminRequiredMixin, View):
    def get(self, request):
        qs = InstallRecord.objects.select_related("customer")
        return render(request, "control_center/install_list.html", {
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "nav": "installs",
        })


class InstallFormView(ControlAdminRequiredMixin, View):
    CHECKLIST_FIELDS = (
        "checklist_dns", "checklist_ssl", "checklist_env", "checklist_migrate",
        "checklist_admin", "checklist_sms", "checklist_payment", "checklist_handover",
    )

    def get(self, request, pk=None):
        obj = get_object_or_404(InstallRecord, pk=pk) if pk else InstallRecord(product_mode="academy")
        return render(request, "control_center/install_form.html", {
            "obj": obj,
            "title": "ویرایش نصب" if pk else "ثبت نصب جدید",
            "customers": Customer.objects.order_by("organization_name"),
            "nav": "installs",
        })

    def post(self, request, pk=None):
        obj = get_object_or_404(InstallRecord, pk=pk) if pk else InstallRecord()
        obj.customer_id = request.POST.get("customer_id")
        obj.domain = request.POST.get("domain", "").strip()
        obj.panel_url = request.POST.get("panel_url", "").strip()
        obj.server_host = request.POST.get("server_host", "").strip()
        obj.product_mode = request.POST.get("product_mode", "academy").strip()
        obj.app_version = request.POST.get("app_version", "").strip()
        obj.database_note = request.POST.get("database_note", "").strip()
        obj.install_notes = request.POST.get("install_notes", "").strip()
        upgraded = request.POST.get("last_upgraded_at") or None
        obj.last_upgraded_at = upgraded or None
        for field in self.CHECKLIST_FIELDS:
            setattr(obj, field, request.POST.get(field) == "on")
        if not obj.domain or not obj.customer_id:
            messages.error(request, "مشتری و دامنه الزامی هستند.")
            return redirect(request.path)
        obj.save()
        messages.success(request, "نصب ذخیره شد.")
        return redirect("control_center:install_list")
