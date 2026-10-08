import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.academy.mixins import AdminRequiredMixin
from django.db import transaction
from django.utils import timezone

from ..models import Course, Exam, Question, Choice, ExamAttempt, StudentAnswer, StudentEnrollment
from ..services.exam_service import create_attempt, submit_attempt, auto_grade_attempt


class ExamListView(AdminRequiredMixin, View):
    def get(self, request):
        courses = Course.objects.filter(teacher__isnull=False).distinct()
        selected_course_id = request.GET.get('course')
        if selected_course_id:
            try:
                selected_course_id = int(selected_course_id)
            except (ValueError, TypeError):
                selected_course_id = None
        if selected_course_id:
            exams = Exam.objects.filter(course_id=selected_course_id).order_by('-created_at')
        else:
            exams = Exam.objects.all().order_by('-created_at')
        return render(request, 'academy/dashboard/exam_list.html', {
            'exams': exams,
            'courses': courses,
            'selected_course_id': selected_course_id,
        })


class ExamCreateView(AdminRequiredMixin, View):
    def get(self, request):
        courses = Course.objects.filter(is_active=True)
        return render(request, 'academy/dashboard/exam_form.html', {
            'courses': courses,
            'exam': None,
        })

    def post(self, request):
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        if not title or not course_id:
            messages.error(request, "عنوان و دوره الزامی هستند.")
            return redirect('academy:exam_create')

        course = self.school_object_or_404(Course, id=course_id)
        try:
            duration_minutes = int(request.POST.get('duration_minutes', 30))
            pass_score_percent = int(request.POST.get('pass_score_percent', 50))
            attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        except (ValueError, TypeError):
            messages.error(request, "مقادیر عددی وارد شده معتبر نیستند.")
            return redirect('academy:exam_create')
        exam = Exam(
            course=course,
            title=title,
            description=request.POST.get('description', ''),
            exam_type=request.POST.get('exam_type', 'quiz'),
            duration_minutes=duration_minutes,
            pass_score_percent=pass_score_percent,
            shuffle_questions=request.POST.get('shuffle_questions') == 'on',
            shuffle_choices=request.POST.get('shuffle_choices') == 'on',
            show_result_immediately=request.POST.get('show_result_immediately') == 'on',
            show_answers_after=request.POST.get('show_answers_after') == 'on',
            attempts_allowed=attempts_allowed,
            is_active=request.POST.get('is_active') == 'on',
            random_question_count=request.POST.get('random_question_count') or None,
        )
        sd = request.POST.get('start_date')
        ed = request.POST.get('end_date')
        if sd:
            from ..utils.date_helper import to_gregorian
            exam.start_date = to_gregorian(sd)
        if ed:
            from ..utils.date_helper import to_gregorian
            exam.end_date = to_gregorian(ed)
        exam.save()
        messages.success(request, f"آزمون «{title}» با موفقیت ایجاد شد.")
        return redirect('academy:exam_questions', exam_id=exam.id)


class ExamEditView(AdminRequiredMixin, View):
    def get(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        courses = Course.objects.filter(is_active=True)
        return render(request, 'academy/dashboard/exam_form.html', {
            'exam': exam,
            'courses': courses,
        })

    def post(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        exam.title = request.POST.get('title', exam.title)
        exam.description = request.POST.get('description', '')
        exam.exam_type = request.POST.get('exam_type', exam.exam_type)
        try:
            exam.duration_minutes = int(request.POST.get('duration_minutes', 30))
            exam.pass_score_percent = int(request.POST.get('pass_score_percent', 50))
            exam.attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        except (ValueError, TypeError):
            messages.error(request, "مقادیر عددی وارد شده معتبر نیستند.")
            return redirect('academy:exam_edit', exam_id=exam.id)
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
            from ..utils.date_helper import to_gregorian
            exam.start_date = to_gregorian(sd)
        if ed:
            from ..utils.date_helper import to_gregorian
            exam.end_date = to_gregorian(ed)
        exam.save()
        messages.success(request, "آزمون با موفقیت بروزرسانی شد.")
        return redirect('academy:exam_list')


class ExamDeleteView(AdminRequiredMixin, View):
    def post(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        exam.delete()
        messages.success(request, "آزمون با موفقیت حذف شد.")
        return redirect('academy:exam_list')


class ExamQuestionsView(AdminRequiredMixin, View):
    def get(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        questions = exam.questions.all()
        return render(request, 'academy/dashboard/exam_questions.html', {
            'exam': exam,
            'questions': questions,
        })

    def post(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')

        if action == 'add_question':
            qtype = request.POST.get('question_type')
            title = request.POST.get('title')
            if title and qtype:
                try:
                    points = int(request.POST.get('points', 1))
                except (ValueError, TypeError):
                    points = 1
                max_order = exam.questions.aggregate(m=models.Max('order'))['m'] or 0
                Question.objects.create(
                    exam=exam,
                    question_type=qtype,
                    title=title,
                    points=points,
                    order=max_order + 1,
                    is_required=True,
                )
                messages.success(request, "سوال اضافه شد.")

        elif action == 'edit_question':
            qid = request.POST.get('question_id')
            if qid:
                question = Question.objects.filter(id=qid, exam=exam).first()
                if question:
                    question.title = request.POST.get('title', question.title)
                    question.points = int(request.POST.get('points', question.points))
                    question.save()
                    messages.success(request, "سوال بروزرسانی شد.")

        elif action == 'delete_question':
            qid = request.POST.get('question_id')
            if qid:
                Question.objects.filter(id=qid, exam=exam).delete()
                messages.success(request, "سوال حذف شد.")

        elif action == 'reorder':
            order_data = request.POST.get('order_data', '[]')
            try:
                order_list = json.loads(order_data)
                for item in order_list:
                    Question.objects.filter(id=item['id'], exam=exam).update(order=item['order'])
                return redirect('academy:exam_questions', exam_id=exam.id)
            except (json.JSONDecodeError, KeyError):
                messages.error(request, "خطا در ذخیره ترتیب.")

        return redirect('academy:exam_questions', exam_id=exam.id)


class QuestionChoicesView(AdminRequiredMixin, View):
    def get(self, request, question_id):
        question = self.school_object_or_404(
            Question, id=question_id,
        )
        choices = question.choices.all()
        return render(request, 'academy/dashboard/question_choices.html', {
            'question': question,
            'choices': choices,
        })

    def post(self, request, question_id):
        question = self.school_object_or_404(
            Question, id=question_id,
        )
        action = request.POST.get('action')

        if action == 'add_choice':
            text = request.POST.get('text')
            if text:
                max_order = question.choices.aggregate(m=models.Max('order'))['m'] or 0
                choice = Choice.objects.create(
                    question=question,
                    text=text,
                    is_correct=request.POST.get('is_correct') == 'on',
                    order=max_order + 1,
                )
                if request.FILES.get('image'):
                    choice.image = request.FILES['image']
                    choice.save()
                messages.success(request, "گزینه اضافه شد.")

        elif action == 'edit_choice':
            cid = request.POST.get('choice_id')
            choice = get_object_or_404(Choice, id=cid, question=question)
            choice.text = request.POST.get('text', choice.text)
            choice.is_correct = request.POST.get('is_correct') == 'on'
            if request.FILES.get('image'):
                choice.image = request.FILES['image']
            choice.save()
            messages.success(request, "گزینه بروزرسانی شد.")

        elif action == 'delete_choice':
            cid = request.POST.get('choice_id')
            Choice.objects.filter(id=cid, question=question).delete()
            messages.success(request, "گزینه حذف شد.")

        elif action == 'set_correct':
            cid = request.POST.get('choice_id')
            if question.question_type in ('multiple_choice', 'true_false'):
                question.choices.update(is_correct=False)
                Choice.objects.filter(id=cid, question=question).update(is_correct=True)
            else:
                choice = get_object_or_404(Choice, id=cid, question=question)
                choice.is_correct = not choice.is_correct
                choice.save()
            messages.success(request, "گزینه صحیح تنظیم شد.")

        return redirect('academy:question_choices', question_id=question.id)


class ExamResultsView(AdminRequiredMixin, View):
    def get(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        attempts = exam.attempts.select_related('student').order_by('-score', 'start_time')
        return render(request, 'academy/dashboard/exam_results.html', {
            'exam': exam,
            'attempts': attempts,
            'stats': self.get_stats(attempts, exam),
        })

    def get_stats(self, attempts, exam):
        total = attempts.count()
        if total == 0:
            return {'total': 0}
        graded = [a for a in attempts if a.status == 'graded']
        passed = [a for a in graded if a.is_passed]
        scores = [a.score for a in graded if a.score is not None]
        return {
            'total': total,
            'graded': len(graded),
            'passed': len(passed),
            'failed': len(graded) - len(passed),
            'pass_rate': round(len(passed) / len(graded) * 100, 1) if graded else 0,
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'total_score': exam.total_score,
        }

    def post(self, request, exam_id):
        exam = self.school_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')
        attempt_id = request.POST.get('attempt_id')

        if action == 'grade_essay':
            attempt = get_object_or_404(ExamAttempt, id=attempt_id, exam=exam)
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
            exam.show_result_immediately = True
            exam.save()
            messages.success(request, "نتایج برای هنرجویان منتشر شد.")

        return redirect('academy:exam_results', exam_id=exam.id)


class AttemptDetailView(AdminRequiredMixin, View):
    def get(self, request, attempt_id):
        attempt = self.school_object_or_404(
            ExamAttempt,
            id=attempt_id
        )
        attempt = ExamAttempt.objects.select_related('exam', 'student', 'exam__course').get(id=attempt.id)
        answers = attempt.answers.select_related('question').prefetch_related('selected_choices')
        return render(request, 'academy/dashboard/attempt_detail.html', {
            'attempt': attempt,
            'answers': answers,
        })


class TakeExamView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        # Find the student from the logged-in user
        student = StudentEnrollment.objects.filter(
            user_account__user=request.user,
            active_enrollments__course=exam.course
        ).first()
        if not student:
            messages.error(request, "شما در این دوره ثبت‌نام ندارید.")
            return redirect('student:dashboard')

        # Check existing attempts
        existing = ExamAttempt.objects.filter(exam=exam, student=student)
        if exam.attempts_allowed > 0 and existing.filter(status__in=('submitted', 'graded')).count() >= exam.attempts_allowed:
            messages.error(request, "تعداد دفعات مجاز شما به پایان رسیده است.")
            return redirect('student:dashboard')

        # Resume in-progress attempt
        current = existing.filter(status='in_progress').first()
        if current:
            if current.is_time_up:
                submit_attempt(current, {})
                messages.warning(request, "زمان شما به پایان رسید. پاسخ‌ها به صورت خودکار ثبت شدند.")
                return redirect('academy:exam_result', attempt_id=current.id)
            return render(request, 'student/take_exam.html', {
                'exam': exam,
                'attempt': current,
            })

        # Create new attempt
        attempt = create_attempt(exam, student, request)
        return render(request, 'student/take_exam.html', {
            'exam': exam,
            'attempt': attempt,
        })

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        attempt_id = request.POST.get('attempt_id')
        attempt = get_object_or_404(ExamAttempt, id=attempt_id, exam=exam)
        student = StudentEnrollment.objects.filter(
            user_account__user=request.user,
            active_enrollments__course=exam.course
        ).first()

        if not student or attempt.student != student:
            messages.error(request, "شما دسترسی به این آزمون ندارید.")
            return redirect('student:dashboard')

        # بررسی وضعیت آزمون
        if attempt.status != 'in_progress':
            messages.warning(request, "این آزمون قبلاً ارسال شده است.")
            return redirect('academy:exam_result', attempt_id=attempt.id)

        # بررسی زمان باقی‌مانده
        if attempt.is_time_up:
            submit_attempt(attempt, {}, request)
            messages.warning(request, "زمان شما به پایان رسید. پاسخ‌ها به صورت خودکار ثبت شدند.")
            return redirect('academy:exam_result', attempt_id=attempt.id)

        attempt = submit_attempt(attempt, request.POST, request)
        messages.success(request, "پاسخ‌های شما با موفقیت ثبت شد.")
        return redirect('academy:exam_result', attempt_id=attempt.id)


class ExamResultView(LoginRequiredMixin, View):
    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            ExamAttempt.objects.select_related('exam', 'student', 'exam__course'),
            id=attempt_id
        )
        student = StudentEnrollment.objects.filter(
            user_account__user=request.user
        ).first()
        is_owner = student and attempt.student == student
        is_teacher = request.user.role == 'TEACHER' or request.user.is_staff

        if not is_owner and not is_teacher:
            messages.error(request, "دسترسی غیرمجاز.")
            return redirect('student:dashboard')

        answers = attempt.answers.select_related('question').prefetch_related('selected_choices', 'question__choices')

        template = 'student/exam_result.html' if is_owner else 'academy/dashboard/exam_result.html'
        return render(request, template, {
            'attempt': attempt,
            'answers': answers,
            'is_owner': is_owner,
            'show_answers': attempt.exam.show_answers_after or is_teacher,
        })


class StudentExamListView(LoginRequiredMixin, View):
    def get(self, request):
        student = StudentEnrollment.objects.filter(
            user_account__user=request.user
        ).first()
        if not student:
            messages.error(request, "پروفایل هنرجو یافت نشد.")
            return redirect('student:dashboard')

        courses = Course.objects.filter(
            active_enrollments__student=student, is_active=True
        )
        exams = Exam.objects.filter(
            course__in=courses, is_active=True
        ).order_by('-created_at')

        exam_data = []
        for exam in exams:
            attempts = ExamAttempt.objects.filter(exam=exam, student=student)
            best = attempts.filter(status='graded').order_by('-score').first()
            remaining = exam.attempts_allowed - attempts.filter(status__in=('submitted', 'graded')).count()
            exam_data.append({
                'exam': exam,
                'best_attempt': best,
                'remaining_attempts': max(0, remaining),
                'has_in_progress': attempts.filter(status='in_progress').exists(),
                'can_take': remaining > 0 or exam.attempts_allowed == 0,
            })

        return render(request, 'academy/dashboard/student_exams.html', {
            'exam_data': exam_data,
            'student': student,
        })


import django.db.models as models
