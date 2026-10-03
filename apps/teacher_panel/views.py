from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
import django.db.models as models

from apps.academy.models import Course, Session, StudentEnrollment, Attendance, Exam, Question, Choice, ExamAttempt, FillBlankAnswer
from apps.academy.models.material import SessionMaterial
from apps.academy.services.attendance_service import AttendanceService
from apps.academy.services.finance_service import FinanceService
from apps.academy.services.exam_service import create_attempt, submit_attempt, auto_grade_attempt
from apps.academy.utils.date_helper import to_gregorian
import json

from apps.users.mixins import RoleRequiredMixin


class TeacherRequiredMixin(RoleRequiredMixin):
    role = 'TEACHER'
    panel = 'teacher'
    login_url = '/auth/teacher/login/'


class TeacherDashboardView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        stats = FinanceService.get_teacher_earnings(teacher.id)
        upcoming_sessions = Session.objects.filter(
            course__teacher=teacher
        ).order_by('date')[:5]
        return render(request, 'teacher/dashboard.html', {
            'teacher': teacher,
            'stats': stats,
            'upcoming_sessions': upcoming_sessions,
        })


class TeacherCourseListView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher).prefetch_related('sessions', 'active_enrollments')
        return render(request, 'teacher/course_list.html', {'courses': courses})


class TeacherStudentListView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        teacher = request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        students = StudentEnrollment.objects.filter(
            active_enrollments__course=course
        ).prefetch_related('attendances')
        return render(request, 'teacher/student_list.html', {
            'course': course,
            'students': students,
        })


class TeacherAttendanceView(TeacherRequiredMixin, View):
    def get(self, request, session_id):
        teacher = request.user.teacher_profile
        session = get_object_or_404(Session, id=session_id, course__teacher=teacher)
        data = AttendanceService.get_sheet(session_id)
        return render(request, 'teacher/attendance_sheet.html', data)

    def post(self, request, session_id):
        teacher = request.user.teacher_profile
        session = get_object_or_404(Session, id=session_id, course__teacher=teacher)
        attendance_data = {}
        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                try:
                    student_id = int(key.replace('attendance_', ''))
                except (ValueError, TypeError):
                    continue
                attendance_data[student_id] = value
        AttendanceService.bulk_save(session_id, attendance_data)
        messages.success(request, f'حضور و غیاب جلسه {session.session_number} ثبت شد.')
        return redirect('teacher:course_list')


class TeacherEarningsView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        stats = FinanceService.get_teacher_earnings(teacher.id)
        return render(request, 'teacher/earnings.html', {
            'teacher': teacher,
            'stats': stats,
        })


class TeacherProfileView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        from apps.academy.models import Session, CourseEnrollment
        courses = Course.objects.filter(teacher=teacher)
        total_sessions = Session.objects.filter(course__teacher=teacher).count()
        total_enrolled = CourseEnrollment.objects.filter(course__teacher=teacher).values('student').distinct().count()
        return render(request, 'teacher/profile.html', {
            'teacher': teacher,
            'courses': courses,
            'total_sessions': total_sessions,
            'total_enrolled': total_enrolled,
        })


# ─── آزمون‌ها (پنل استاد) ─────────────────────────────────────────────

class TeacherExamListView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        selected_course_id = request.GET.get('course')
        if selected_course_id:
            try:
                selected_course_id = int(selected_course_id)
            except (ValueError, TypeError):
                selected_course_id = None
        if selected_course_id:
            exams = Exam.objects.filter(course_id=selected_course_id, course__teacher=teacher).order_by('-created_at')
        else:
            exams = Exam.objects.filter(course__teacher=teacher).order_by('-created_at')
        return render(request, 'teacher/exam_list.html', {
            'exams': exams,
            'courses': courses,
            'selected_course_id': selected_course_id,
        })


class TeacherExamCreateView(TeacherRequiredMixin, View):
    def get(self, request):
        teacher = request.user.teacher_profile
        courses = Course.objects.filter(teacher=teacher, is_active=True)
        return render(request, 'teacher/exam_form.html', {'courses': courses, 'exam': None})

    def post(self, request):
        teacher = request.user.teacher_profile
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        if not title or not course_id:
            messages.error(request, "عنوان و دوره الزامی هستند.")
            return redirect('teacher:exam_create')
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        try:
            duration_minutes = int(request.POST.get('duration_minutes', 30))
            pass_score_percent = int(request.POST.get('pass_score_percent', 50))
            attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        except (ValueError, TypeError):
            messages.error(request, "مقادیر عددی وارد شده معتبر نیستند.")
            return redirect('teacher:exam_create')
        exam = Exam(course=course, title=title, description=request.POST.get('description', ''),
            exam_type=request.POST.get('exam_type', 'quiz'),
            duration_minutes=duration_minutes,
            pass_score_percent=pass_score_percent,
            shuffle_questions=request.POST.get('shuffle_questions') == 'on',
            shuffle_choices=request.POST.get('shuffle_choices') == 'on',
            show_result_immediately=request.POST.get('show_result_immediately') == 'on',
            show_answers_after=request.POST.get('show_answers_after') == 'on',
            attempts_allowed=attempts_allowed,
            is_active=request.POST.get('is_active') == 'on',
            random_question_count=request.POST.get('random_question_count') or None)
        sd = request.POST.get('start_date')
        ed = request.POST.get('end_date')
        if sd:
            from apps.academy.utils.date_helper import to_gregorian
            exam.start_date = to_gregorian(sd)
        if ed:
            from apps.academy.utils.date_helper import to_gregorian
            exam.end_date = to_gregorian(ed)
        exam.save()
        messages.success(request, f'آزمون «{title}» با موفقیت ایجاد شد.')
        return redirect('teacher:exam_questions', exam_id=exam.id)


class TeacherExamEditView(TeacherRequiredMixin, View):
    def get(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        courses = Course.objects.filter(teacher=teacher, is_active=True)
        return render(request, 'teacher/exam_form.html', {'exam': exam, 'courses': courses})

    def post(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        exam.title = request.POST.get('title', exam.title)
        exam.description = request.POST.get('description', '')
        exam.exam_type = request.POST.get('exam_type', exam.exam_type)
        try:
            exam.duration_minutes = int(request.POST.get('duration_minutes', 30))
            exam.pass_score_percent = int(request.POST.get('pass_score_percent', 50))
            exam.attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        except (ValueError, TypeError):
            messages.error(request, "مقادیر عددی وارد شده معتبر نیستند.")
            return redirect('teacher:exam_edit', exam_id=exam.id)
        exam.shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        exam.shuffle_choices = request.POST.get('shuffle_choices') == 'on'
        exam.show_result_immediately = request.POST.get('show_result_immediately') == 'on'
        exam.show_answers_after = request.POST.get('show_answers_after') == 'on'
        exam.attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        exam.is_active = request.POST.get('is_active') == 'on'
        exam.random_question_count = request.POST.get('random_question_count') or None
        sd = request.POST.get('start_date')
        ed = request.POST.get('end_date')
        if sd:
            from apps.academy.utils.date_helper import to_gregorian
            exam.start_date = to_gregorian(sd)
        if ed:
            from apps.academy.utils.date_helper import to_gregorian
            exam.end_date = to_gregorian(ed)
        exam.save()
        messages.success(request, 'آزمون بروزرسانی شد.')
        return redirect('teacher:exam_list')


class TeacherExamDeleteView(TeacherRequiredMixin, View):
    def post(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        exam.delete()
        messages.success(request, 'آزمون حذف شد.')
        return redirect('teacher:exam_list')


class TeacherExamQuestionsView(TeacherRequiredMixin, View):
    def get(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        questions = exam.questions.all()
        return render(request, 'teacher/exam_questions.html', {'exam': exam, 'questions': questions})

    def post(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        action = request.POST.get('action')
        if action == 'add_question':
            qtype = request.POST.get('question_type')
            title = request.POST.get('title')
            if title and qtype:
                from django.db.models import Max
                try:
                    points = int(request.POST.get('points', 1))
                except (ValueError, TypeError):
                    points = 1
                max_order = exam.questions.aggregate(m=Max('order'))['m'] or 0
                Question.objects.create(exam=exam, question_type=qtype, title=title,
                    points=points, order=max_order + 1, is_required=True)
                messages.success(request, 'سوال اضافه شد.')
        elif action == 'delete_question':
            qid = request.POST.get('question_id')
            if qid:
                Question.objects.filter(id=qid, exam=exam).delete()
                messages.success(request, 'سوال حذف شد.')
        elif action == 'reorder':
            order_data = request.POST.get('order_data', '[]')
            try:
                for item in json.loads(order_data):
                    Question.objects.filter(id=item['id'], exam=exam).update(order=item['order'])
            except (json.JSONDecodeError, KeyError):
                messages.error(request, 'خطا در ذخیره ترتیب.')
        return redirect('teacher:exam_questions', exam_id=exam.id)


class TeacherQuestionChoicesView(TeacherRequiredMixin, View):
    def get(self, request, question_id):
        teacher = request.user.teacher_profile
        question = get_object_or_404(Question, id=question_id, exam__course__teacher=teacher)
        choices = question.choices.all()
        fillblank_answers = question.fill_blank_answers.all()
        return render(request, 'teacher/question_choices.html', {
            'question': question, 'choices': choices, 'fillblank_answers': fillblank_answers
        })

    def post(self, request, question_id):
        teacher = request.user.teacher_profile
        question = get_object_or_404(Question, id=question_id, exam__course__teacher=teacher)
        action = request.POST.get('action')
        if action == 'add_choice':
            text = request.POST.get('text')
            if text:
                from django.db.models import Max
                max_order = question.choices.aggregate(m=Max('order'))['m'] or 0
                choice = Choice.objects.create(question=question, text=text,
                    is_correct=request.POST.get('is_correct') == 'on', order=max_order + 1)
                if request.FILES.get('image'):
                    choice.image = request.FILES['image']
                    choice.save()
                messages.success(request, 'گزینه اضافه شد.')
        elif action == 'edit_choice':
            cid = request.POST.get('choice_id')
            choice = get_object_or_404(Choice, id=cid, question=question)
            choice.text = request.POST.get('text', choice.text)
            choice.is_correct = request.POST.get('is_correct') == 'on'
            if request.FILES.get('image'):
                choice.image = request.FILES['image']
            choice.save()
            messages.success(request, 'گزینه بروزرسانی شد.')
        elif action == 'delete_choice':
            cid = request.POST.get('choice_id')
            Choice.objects.filter(id=cid, question=question).delete()
            messages.success(request, 'گزینه حذف شد.')
        elif action == 'set_correct':
            cid = request.POST.get('choice_id')
            if question.question_type in ('multiple_choice', 'true_false'):
                question.choices.update(is_correct=False)
                Choice.objects.filter(id=cid, question=question).update(is_correct=True)
            else:
                choice = get_object_or_404(Choice, id=cid, question=question)
                choice.is_correct = not choice.is_correct
                choice.save()
            messages.success(request, 'گزینه صحیح تنظیم شد.')
        elif action == 'add_fillblank_answer':
            answer_text = request.POST.get('answer_text')
            if answer_text:
                from django.db.models import Max
                max_order = question.fill_blank_answers.aggregate(m=Max('order'))['m'] or 0
                FillBlankAnswer.objects.create(
                    question=question,
                    answer_text=answer_text,
                    acceptable_alternatives=request.POST.get('acceptable_alternatives', ''),
                    order=max_order + 1
                )
                messages.success(request, 'پاسخ صحیح اضافه شد.')
        elif action == 'delete_fillblank_answer':
            fa_id = request.POST.get('fillblank_id')
            FillBlankAnswer.objects.filter(id=fa_id, question=question).delete()
            messages.success(request, 'پاسخ حذف شد.')
        return redirect('teacher:question_choices', question_id=question.id)


# ─── جلسات (پنل استاد) ─────────────────────────────────────────────

class TeacherSessionListView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        teacher = request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        sessions = course.sessions.order_by('session_number')
        return render(request, 'teacher/session_list.html', {
            'course': course,
            'sessions': sessions,
        })


class TeacherSessionCreateView(TeacherRequiredMixin, View):
    def post(self, request, course_id):
        teacher = request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)

        title = request.POST.get('title', f"جلسه {course.sessions.count() + 1}")
        start_date = to_gregorian(request.POST.get('date'))
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None
        location = request.POST.get('location', '').strip() or None
        description = request.POST.get('description', '')
        meeting_type = request.POST.get('meeting_type', 'none')
        meeting_link = request.POST.get('meeting_link') or None
        repeat_weeks = int(request.POST.get('repeat_weeks', 1) or 1)
        repeat_days = request.POST.getlist('repeat_days')

        if not start_date:
            messages.error(request, "تاریخ جلسه الزامی است.")
            return redirect('teacher:session_list', course_id=course_id)

        session_number = course.sessions.count() + 1
        created_count = 0

        if repeat_weeks > 1 and repeat_days:
            # Create recurring sessions
            from datetime import timedelta
            for week in range(repeat_weeks):
                for day_str in repeat_days:
                    try:
                        day_num = int(day_str)
                    except (ValueError, TypeError):
                        continue
                    # Calculate the date for this weekday in this week
                    session_date = start_date + timedelta(weeks=week, days=(day_num - start_date.weekday()) % 7)
                    if session_date < start_date:
                        continue
                    Session.objects.create(
                        course=course, title=title, session_number=session_number,
                        date=session_date, start_time=start_time, end_time=end_time,
                        location=location, description=description, meeting_type=meeting_type,
                        meeting_link=meeting_link if meeting_type not in ('none', 'jitsi') else None,
                    )
                    session_number += 1
                    created_count += 1
        else:
            # Single session
            Session.objects.create(
                course=course, title=title, session_number=session_number,
                date=start_date, start_time=start_time, end_time=end_time,
                location=location, description=description, meeting_type=meeting_type,
                meeting_link=meeting_link if meeting_type not in ('none', 'jitsi') else None,
            )
            created_count = 1

        messages.success(request, f"{created_count} جلسه با موفقیت ایجاد شد.")
        return redirect('teacher:session_list', course_id=course_id)


# ─── محتوای جلسات (پنل استاد) ─────────────────────────────────────

class TeacherMaterialListView(TeacherRequiredMixin, View):
    def get(self, request, session_id):
        teacher = request.user.teacher_profile
        session = get_object_or_404(Session, id=session_id, course__teacher=teacher)
        materials = session.materials.all()
        return render(request, 'teacher/material_list.html', {
            'session': session,
            'materials': materials,
        })

    def post(self, request, session_id):
        teacher = request.user.teacher_profile
        session = get_object_or_404(Session, id=session_id, course__teacher=teacher)
        action = request.POST.get('action')

        if action == 'add':
            title = request.POST.get('title')
            if not title:
                messages.error(request, "عنوان محتوا الزامی است.")
                return redirect('teacher:material_list', session_id=session_id)
            from django.db.models import Max
            max_order = session.materials.aggregate(m=Max('order'))['m'] or 0
            SessionMaterial.objects.create(
                course=session.course,
                session=session,
                title=title,
                description=request.POST.get('description', ''),
                material_type=request.POST.get('material_type', 'file'),
                file=request.FILES.get('file'),
                link_url=request.POST.get('link_url', ''),
                order=max_order + 1,
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f"محتوا «{title}» اضافه شد.")

        elif action == 'edit':
            mid = request.POST.get('material_id')
            mat = get_object_or_404(SessionMaterial, id=mid, session=session)
            mat.title = request.POST.get('title', mat.title)
            mat.description = request.POST.get('description', '')
            mat.material_type = request.POST.get('material_type', mat.material_type)
            if request.FILES.get('file'):
                mat.file = request.FILES['file']
            mat.link_url = request.POST.get('link_url', '')
            mat.is_active = request.POST.get('is_active') == 'on'
            mat.save()
            messages.success(request, "محتوا بروزرسانی شد.")

        elif action == 'delete':
            mid = request.POST.get('material_id')
            SessionMaterial.objects.filter(id=mid, session=session).delete()
            messages.success(request, "محتوا حذف شد.")

        return redirect('teacher:material_list', session_id=session_id)


class TeacherCourseMaterialListView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        teacher = request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        materials = SessionMaterial.objects.filter(
            models.Q(course=course) | models.Q(session__course=course)
        ).select_related('session').order_by('-created_at')
        return render(request, 'teacher/course_materials.html', {
            'course': course,
            'materials': materials,
        })


class TeacherExamResultsView(TeacherRequiredMixin, View):
    def get(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        attempts = exam.attempts.select_related('student').order_by('-score', 'start_time')
        return render(request, 'teacher/exam_results.html', {
            'exam': exam, 'attempts': attempts,
            'stats': self.get_stats(attempts, exam),
        })

    def get_stats(self, attempts, exam):
        total = attempts.count()
        if total == 0:
            return {'total': 0}
        graded = [a for a in attempts if a.status == 'graded']
        passed = [a for a in graded if a.is_passed]
        scores = [a.score for a in graded if a.score is not None]
        return {'total': total, 'graded': len(graded), 'passed': len(passed),
            'failed': len(graded) - len(passed),
            'pass_rate': round(len(passed) / len(graded) * 100, 1) if graded else 0,
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'total_score': exam.total_score}

    def post(self, request, exam_id):
        teacher = request.user.teacher_profile
        exam = get_object_or_404(Exam, id=exam_id, course__teacher=teacher)
        action = request.POST.get('action')
        attempt_id = request.POST.get('attempt_id')
        if action == 'grade_essay':
            attempt = get_object_or_404(ExamAttempt, id=attempt_id, exam=exam)
            for answer in attempt.answers.filter(question__question_type='essay', score__isnull=True):
                score_key = f'score_{answer.id}'
                if score_key in request.POST:
                    val = request.POST.get(score_key)
                    if val:
                        try:
                            answer.score = float(val)
                        except (ValueError, TypeError):
                            continue
                        answer.graded_by = request.user
                        answer.graded_at = timezone.now()
                        answer.save()
            auto_grade_attempt(attempt)
            messages.success(request, 'نمرات تشریحی ثبت شد.')
        elif action == 'release_results':
            exam.show_result_immediately = True
            exam.save()
            messages.success(request, 'نتایج برای هنرجویان منتشر شد.')
        return redirect('teacher:exam_results', exam_id=exam.id)


class TeacherAttemptDetailView(TeacherRequiredMixin, View):
    def get(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt.objects.select_related('exam', 'student', 'exam__course'),
            id=attempt_id, exam__course__teacher=request.user.teacher_profile)
        answers = attempt.answers.select_related('question').prefetch_related('selected_choices')
        return render(request, 'teacher/attempt_detail.html', {'attempt': attempt, 'answers': answers})

    def post(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt.objects.select_related('exam', 'student', 'exam__course'),
            id=attempt_id, exam__course__teacher=request.user.teacher_profile)
        action = request.POST.get('action')

        if action == 'grade_essay':
            answers = attempt.answers.filter(question__question_type='essay', score__isnull=True)
            for answer in answers:
                score_key = f'score_{answer.id}'
                if score_key in request.POST:
                    val = request.POST.get(score_key)
                    if val:
                        try:
                            answer.score = float(val)
                        except (ValueError, TypeError):
                            continue
                        answer.graded_by = request.user
                        answer.graded_at = timezone.now()
                        answer.save()
            auto_grade_attempt(attempt)
            messages.success(request, "نمرات با موفقیت ثبت شد.")

        elif action == 'release_results':
            attempt.exam.show_result_immediately = True
            attempt.exam.save(update_fields=['show_result_immediately'])
            messages.success(request, "نتایج برای هنرجو منتشر شد.")

        return redirect('teacher:attempt_detail', attempt_id=attempt.id)
