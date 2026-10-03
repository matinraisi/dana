from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin

from ..models import DiscountCode


class DiscountCodeListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        codes = self.filter_by_school(DiscountCode.objects.all())
        return render(request, 'academy/dashboard/discount_list.html', {
            'codes': codes,
        })


class DiscountCodeCreateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        from ..models import Course
        courses = self.filter_by_school(Course.objects.all())
        return render(request, 'academy/dashboard/discount_create.html', {
            'courses': courses,
        })

    def post(self, request):
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '')
        discount_type = request.POST.get('discount_type', 'percent')
        discount_value = request.POST.get('discount_value')
        max_uses = request.POST.get('max_uses', 0)
        min_amount = request.POST.get('min_amount', 0)
        course_id = request.POST.get('course_id') or None
        valid_from = request.POST.get('valid_from') or None
        valid_until = request.POST.get('valid_until') or None

        if not code or not discount_value:
            messages.error(request, "کد تخفیف و مقدار تخفیف الزامی هستند.")
            return redirect('academy:discount_create')

        if DiscountCode.objects.filter(code=code).exists():
            messages.error(request, f"کد تخفیف «{code}» از قبل موجود است.")
            return redirect('academy:discount_create')

        try:
            discount_value = int(discount_value)
            max_uses = int(max_uses)
            min_amount = int(min_amount)
        except ValueError:
            messages.error(request, "مقادیر عددی معتبر نیستند.")
            return redirect('academy:discount_create')

        if discount_type == 'percent' and discount_value > 100:
            messages.error(request, "درصد تخفیف نمی‌تواند بیشتر از ۱۰۰ باشد.")
            return redirect('academy:discount_create')

        # بررسی دوره
        course = None
        if course_id:
            from ..models import Course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                pass

        # بررسی تاریخ‌ها
        from django.utils import timezone
        from ..utils.date_helper import to_gregorian
        valid_from_dt = to_gregorian(valid_from) if valid_from else None
        valid_until_dt = to_gregorian(valid_until) if valid_until else None

        if valid_from_dt and valid_until_dt and valid_from_dt > valid_until_dt:
            messages.error(request, "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
            return redirect('academy:discount_create')

        DiscountCode.objects.create(
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            min_amount=min_amount,
            course=course,
            valid_from=valid_from_dt,
            valid_until=valid_until_dt,
            school=getattr(request.user, 'school', None),
            created_by=request.user,
        )

        messages.success(request, f"کد تخفیف «{code}» با موفقیت ایجاد شد.")
        return redirect('academy:discount_list')


class DiscountCodeDeleteView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        code = self.school_object_or_404(DiscountCode, pk=pk)
        code_text = code.code
        code.delete()
        messages.success(request, f"کد تخفیف «{code_text}» حذف شد.")
        return redirect('academy:discount_list')


class DiscountCodeToggleView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        code = self.school_object_or_404(DiscountCode, pk=pk)
        code.is_active = not code.is_active
        code.save(update_fields=['is_active'])
        status = "فعال" if code.is_active else "غیرفعال"
        messages.success(request, f"کد تخفیف «{code.code}» {status} شد.")
        return redirect('academy:discount_list')


class ValidateDiscountAjaxView(AdminRequiredMixin, View):
    """بررسی اعتبار کد تخفیف از طریق AJAX"""
    def get(self, request):
        code_text = request.GET.get('code', '').strip().upper()
        course_id = request.GET.get('course_id')

        if not code_text:
            return JsonResponse({'valid': False, 'message': 'کد تخفیف را وارد کنید'})

        try:
            code = DiscountCode.objects.get(code=code_text)
        except DiscountCode.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'کد تخفیف یافت نشد'})

        # بررسی دوره خاص
        if code.course and course_id and str(code.course.id) != str(course_id):
            return JsonResponse({'valid': False, 'message': 'این کد فقط برای دوره خاصی معتبر است'})

        is_valid, message = code.is_valid
        if not is_valid:
            return JsonResponse({'valid': False, 'message': message})

        return JsonResponse({
            'valid': True,
            'discount_type': code.discount_type,
            'discount_value': code.discount_value,
            'message': f'تخفیف {code.discount_value}{"%" if code.discount_type == "percent" else " تومان"}',
        })
