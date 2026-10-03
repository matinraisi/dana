from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .models import Lead, LeadActivity
from apps.academy.models import Course, StudentEnrollment, CourseEnrollment
from apps.academy.models.accounting import AccountingTransaction, PaymentGateway
from apps.academy.services.sms_service import SmsService
from apps.users.models import User, StudentAccount


class LeadListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        qs = self.filter_by_school(
            Lead.objects.select_related('interested_course', 'assigned_to').order_by('-created_at')
        )
        status_filter = request.GET.get('status')
        search = request.GET.get('q')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone_number__icontains=search)
            )
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'crm/lead_list.html', {
            'page_obj': page_obj,
            'statuses': Lead.STATUS_CHOICES,
            'active_status': status_filter,
        })


class LeadCreateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        courses = self.filter_by_school(Course.objects.filter(status__in=['upcoming', 'open', 'active']))
        return render(request, 'crm/lead_form.html', {
            'courses': courses,
            'source_choices': Lead.SOURCE_CHOICES,
            'status_choices': Lead.STATUS_CHOICES,
        })

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        course_id = request.POST.get('interested_course')
        source = request.POST.get('source', 'other')
        note = request.POST.get('note', '')

        if not all([first_name, last_name, phone_number]):
            messages.error(request, 'نام، نام خانوادگی و شماره موبایل الزامی است.')
            return redirect('crm:lead_create')

        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            interested_course_id=course_id or None,
            source=source,
            note=note,
            assigned_to=request.user,
            school=getattr(request.user, 'school', None),
        )
        messages.success(request, f'سرنخ «{lead.full_name}» ثبت شد.')
        return redirect('crm:lead_list')


class LeadDetailView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        return render(request, 'crm/lead_detail.html', {
            'lead': lead,
            'activities': lead.activities.select_related('created_by').order_by('-created_at'),
            'status_choices': Lead.STATUS_CHOICES,
        })

    def post(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        action = request.POST.get('action')

        if action == 'update_status':
            new_status = request.POST.get('status')
            lead.status = new_status
            lead.save()
            messages.success(request, 'وضعیت سرنخ بروزرسانی شد.')

        elif action == 'add_activity':
            LeadActivity.objects.create(
                lead=lead,
                activity_type=request.POST.get('activity_type', 'note'),
                description=request.POST.get('description', ''),
                created_by=request.user,
            )
            messages.success(request, 'فعالیت ثبت شد.')

        elif action == 'convert_to_student':
            return redirect('crm:lead_convert', pk=lead.id)

        return redirect('crm:lead_detail', pk=pk)


class LeadUpdateStatusView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        lead.status = request.POST.get('status', lead.status)
        lead.save()
        return redirect('crm:lead_detail', pk=pk)


class LeadUpdateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        from apps.academy.models import Course
        courses = Course.objects.filter(status__in=['upcoming', 'open', 'active'])
        return render(request, 'crm/lead_form.html', {
            'lead': lead,
            'courses': courses,
            'status_choices': Lead.STATUS_CHOICES,
            'source_choices': Lead.SOURCE_CHOICES,
            'form': lead,
        })

    def post(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        lead.first_name = request.POST.get('first_name', lead.first_name).strip()
        lead.last_name = request.POST.get('last_name', lead.last_name).strip()
        lead.phone_number = request.POST.get('phone_number', lead.phone_number).strip()
        lead.email = request.POST.get('email', '') or None
        lead.source = request.POST.get('source', lead.source)
        lead.status = request.POST.get('status', lead.status)
        lead.note = request.POST.get('note', '')
        course_id = request.POST.get('interested_course')
        lead.interested_course_id = course_id or None
        lead.save()
        messages.success(request, 'سرنخ بروزرسانی شد.')
        return redirect('crm:lead_detail', pk=pk)


class LeadAddActivityView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        note = request.POST.get('note', '').strip()
        if note:
            LeadActivity.objects.create(
                lead=lead,
                activity_type='note',
                description=note,
                created_by=request.user,
            )
            messages.success(request, 'یادداشت ثبت شد.')
        return redirect('crm:lead_detail', pk=pk)


class LeadConvertView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)
        courses = self.filter_by_school(Course.objects.filter(status__in=['upcoming', 'open', 'active']))
        return render(request, 'crm/lead_convert.html', {
            'lead': lead,
            'courses': courses,
        })

    def post(self, request, pk):
        lead = self.school_object_or_404(Lead, pk=pk)

        # check if already converted
        if lead.converted_student:
            messages.info(request, 'این سرنخ قبلاً به هنرجو تبدیل شده است.')
            return redirect('crm:lead_detail', pk=pk)

        first_name = request.POST.get('first_name', lead.first_name).strip()
        last_name = request.POST.get('last_name', lead.last_name).strip()
        phone_number = request.POST.get('phone_number', lead.phone_number).strip()
        national_code = request.POST.get('national_code', '').strip()
        course_id = request.POST.get('course')
        try:
            total_amount = int(request.POST.get('total_amount') or 0)
            paid_amount = int(request.POST.get('paid_amount') or 0)
        except (ValueError, TypeError):
            messages.error(request, 'مبالغ وارد شده معتبر نیستند.')
            return redirect('crm:lead_convert', pk=pk)

        if not all([first_name, last_name, phone_number, national_code, course_id]):
            messages.error(request, 'پر کردن تمام فیلدهای الزامی است.')
            return render(request, 'crm/lead_convert.html', {
                'lead': lead,
                'courses': Course.objects.filter(status__in=['upcoming', 'open', 'active']),
                'post': request.POST,
            })

        course = get_object_or_404(Course, id=course_id)

        # Create or find student
        existing = StudentEnrollment.objects.filter(phone_number=phone_number).first()
        if existing:
            student = existing
        else:
            student = StudentEnrollment.objects.create(
                first_name=first_name,
                last_name=last_name,
                national_code=national_code,
                phone_number=phone_number,
                school=getattr(request.user, 'school', None),
            )

        # Create enrollment
        if CourseEnrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, f'هنرجو «{student.full_name}» قبلاً در دوره «{course.title}» ثبت‌نام شده است.')
            return redirect('crm:lead_detail', pk=pk)

        payment_method = 'cash' if total_amount == paid_amount and total_amount > 0 else ('installment' if paid_amount > 0 else 'unpaid')
        enroll = CourseEnrollment.objects.create(
            student=student, course=course,
            total_amount=total_amount, paid_amount=paid_amount,
            payment_method=payment_method,
        )

        # Auto-log payment
        if paid_amount > 0:
            default_gateway = PaymentGateway.objects.filter(
                gateway_type__in=['pos', 'gateway', 'card', 'cash'], is_active=True
            ).first()
            AccountingTransaction.objects.create(
                transaction_type='income',
                amount=paid_amount,
                payment_method=payment_method,
                payment_gateway=default_gateway,
                course=course, student=student, enrollment=enroll,
                description=f"پرداخت اولیه ثبت‌نام — {student}",
                transaction_date=timezone.now().date(),
                created_by=request.user,
            )

        # Create user account
        username = f"s_{phone_number}"
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'role': 'STUDENT',
            }
        )
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.role = 'STUDENT'
        user.save()

        StudentAccount.objects.get_or_create(user=user, defaults={'enrollment': student})

        # Send SMS
        login_url = request.build_absolute_uri(reverse('users:student_login'))
        try:
            SmsService.notify_welcome(student, login_url)
        except Exception:
            pass

        # Link lead to student
        lead.converted_student = student
        lead.status = Lead.STATUS_ENROLLED
        lead.save()

        messages.success(request, f'سرنخ «{lead.full_name}» با موفقیت به هنرجو تبدیل شد و در دوره «{course.title}» ثبت‌نام شد.')
        return redirect('crm:lead_detail', pk=pk)
