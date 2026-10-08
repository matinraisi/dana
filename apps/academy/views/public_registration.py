from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.urls import reverse
from django.db import IntegrityError

from ..models import Course, StudentEnrollment, CourseEnrollment, DiscountCode
from ..services.sms_service import SmsService
from apps.users.models import User
from apps.academy.models import StudentAccount
from apps.academy.org import set_organization, get_instance_organization


class PublicCourseRegistrationView(View):
    """صفحه ثبت‌نام آنلاین عمومی برای دوره — بدون نیاز به لاگین."""

    def get(self, request, slug):
        course = get_object_or_404(Course, registration_slug=slug, allow_public_registration=True)
        if course.status not in (Course.STATUS_OPEN, Course.STATUS_UPCOMING):
            return render(request, 'academy/public_registration_closed.html', {'course': course})
        return render(request, 'academy/public_registration.html', {'course': course})

    def post(self, request, slug):
        course = get_object_or_404(Course, registration_slug=slug, allow_public_registration=True)

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        national_code = request.POST.get('national_code', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        education_level = request.POST.get('education_level', '').strip() or None
        discount_code_text = request.POST.get('discount_code', '').strip().upper()

        if not all([first_name, last_name, national_code, phone_number]):
            messages.error(request, 'لطفاً تمامی فیلدهای ستاره‌دار را پر کنید.')
            return render(request, 'academy/public_registration.html', {
                'course': course, 'post': request.POST,
            })

        if len(phone_number) != 11 or not phone_number.startswith('09'):
            messages.error(request, 'شماره موبایل معتبر نیست.')
            return render(request, 'academy/public_registration.html', {
                'course': course, 'post': request.POST,
            })

        # Check for duplicate phone number
        existing_phone = StudentEnrollment.objects.filter(phone_number=phone_number).first()
        if existing_phone and existing_phone.national_code != national_code:
            messages.error(
                request,
                f'این شماره موبایل قبلاً برای «{existing_phone.full_name}» ثبت شده است. '
                'با شماره دیگری ثبت‌نام کنید یا با آموزشگاه تماس بگیرید.'
            )
            return render(request, 'academy/public_registration.html', {
                'course': course, 'post': request.POST,
            })

        # بررسی کد تخفیف
        discount_amount = 0
        discount_code = None
        if discount_code_text:
            try:
                discount_code = DiscountCode.objects.get(code=discount_code_text)
                is_valid, error_msg = discount_code.is_valid
                if not is_valid:
                    messages.error(request, f'کد تخفیف نامعتبر: {error_msg}')
                    return render(request, 'academy/public_registration.html', {
                        'course': course, 'post': request.POST,
                    })
                # بررسی دوره خاص
                if discount_code.course and discount_code.course.id != course.id:
                    messages.error(request, 'این کد تخفیف فقط برای دوره خاصی معتبر است.')
                    return render(request, 'academy/public_registration.html', {
                        'course': course, 'post': request.POST,
                    })
                # بررسی حداقل مبلغ
                if discount_code.min_amount > 0 and course.fee < discount_code.min_amount:
                    messages.error(request, f'حداقل مبلغ سفارش برای این کد {discount_code.min_amount:,} تومان است.')
                    return render(request, 'academy/public_registration.html', {
                        'course': course, 'post': request.POST,
                    })
                # محاسبه تخفیف
                discount_amount = discount_code.calculate_discount(course.fee)
            except DiscountCode.DoesNotExist:
                messages.error(request, 'کد تخفیف یافت نشد.')
                return render(request, 'academy/public_registration.html', {
                    'course': course, 'post': request.POST,
                })

        try:
            student, created = StudentEnrollment.objects.get_or_create(
                national_code=national_code,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone_number,
                    'education_level': education_level,
                    'school': course.school,
                }
            )
        except IntegrityError:
            messages.error(request, 'این کد ملی یا شماره موبایل قبلاً ثبت شده است.')
            return render(request, 'academy/public_registration.html', {
                'course': course, 'post': request.POST,
            })

        if CourseEnrollment.objects.filter(student=student, course=course).exists():
            enrollment = CourseEnrollment.objects.get(student=student, course=course)
            messages.info(request, 'شما قبلاً در این دوره ثبت‌نام کرده‌اید.')
            return render(request, 'academy/public_registration_success.html', {
                'course': course, 'student': student, 'enrollment': enrollment,
            })

        # محاسبه مبلغ نهایی
        final_amount = max(0, course.fee - discount_amount)

        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            total_amount=final_amount,
            paid_amount=0,
            payment_method='unpaid',
        )

        # ثبت استفاده از کد تخفیف
        if discount_code:
            discount_code.apply()

        # ساخت حساب کاربری
        from apps.users.views import DEFAULT_PASSWORD
        username = f"s_{phone_number}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'role': 'STUDENT',
            }
        )
        if created or not user.has_usable_password():
            user.set_password(DEFAULT_PASSWORD)
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.role = 'STUDENT'
        user.save()
        set_organization(user, course.school or get_instance_organization())
        StudentAccount.objects.get_or_create(user=user, defaults={'enrollment': student})

        # لاگین خودکار کاربر
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # ارسال پیامک خوش‌آمد
        login_url = request.build_absolute_uri(reverse('users:student_login'))
        try:
            SmsService.notify_welcome(student, login_url)
        except Exception:
            pass

        return render(request, 'academy/public_registration_success.html', {
            'course': course, 'student': student, 'enrollment': enrollment,
            'discount_amount': discount_amount,
            'installment_1': final_amount // 2,
            'installment_2': final_amount - (final_amount // 2),
        })
