import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import ProvisioningRequest
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
        requests = ProvisioningRequest.objects.all()
        if query:
            requests = requests.filter(
                Q(organization_name__icontains=query)
                | Q(contact_name__icontains=query)
                | Q(phone_number__icontains=query)
            )
        if status:
            requests = requests.filter(status=status)
        page_obj = Paginator(requests, 25).get_page(request.GET.get("page", 1))
        return render(request, self.template_name, {
            "page_obj": page_obj,
            "statuses": ProvisioningRequest.STATUS_CHOICES,
            "active_status": status,
            "query": query,
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
        messages.success(request, "درخواست به‌روزرسانی شد.")
        return redirect("control_center:request_list")
