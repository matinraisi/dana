from django.db import models
from django.utils import timezone
from .course import Course
from .student import StudentEnrollment
from apps.users.models import User


class Exam(models.Model):
    EXAM_TYPES = [
        ('quiz', 'آزمک'),
        ('midterm', 'میان‌ترم'),
        ('final', 'پایان‌ترم'),
        ('assignment', 'تکلیف'),
        ('placement', 'تعیین سطح'),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='exams', verbose_name="دوره"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان آزمون")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    exam_type = models.CharField(
        max_length=20, choices=EXAM_TYPES, default='quiz', verbose_name="نوع آزمون"
    )
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name="مدت زمان (دقیقه)")
    pass_score_percent = models.PositiveIntegerField(
        default=50, verbose_name="درصد قبولی",
        help_text="درصدی از نمره کل که قبولی محسوب می‌شود"
    )
    shuffle_questions = models.BooleanField(default=True, verbose_name="جابجایی تصادفی سوالات")
    shuffle_choices = models.BooleanField(default=True, verbose_name="جابجایی تصادفی گزینه‌ها")
    show_result_immediately = models.BooleanField(
        default=False, verbose_name="نمایش نتیجه بلافاصله پس از آزمون"
    )
    show_answers_after = models.BooleanField(
        default=False, verbose_name="نمایش پاسخ‌های صحیح پس از آزمون"
    )
    attempts_allowed = models.PositiveIntegerField(
        default=1, verbose_name="تعداد دفعات مجاز"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    start_date = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ پایان")
    random_question_count = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="تعداد سوال تصادفی",
        help_text="اگر خالی باشد، همه سوالات نمایش داده می‌شوند"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "آزمون"
        verbose_name_plural = "آزمون‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def total_score(self):
        return self.questions.aggregate(total=models.Sum('points'))['total'] or 0

    @property
    def pass_score(self):
        return int(self.total_score * self.pass_score_percent / 100)

    @property
    def status(self):
        now = timezone.now()
        if not self.is_active:
            return 'disabled'
        if self.start_date and now < self.start_date:
            return 'upcoming'
        if self.end_date and now > self.end_date:
            return 'closed'
        return 'active'

    @property
    def status_display(self):
        status_map = {
            'disabled': 'غیرفعال',
            'upcoming': 'شروع نشده',
            'closed': 'پایان یافته',
            'active': 'فعال',
        }
        return status_map.get(self.status, 'نامشخص')

    @property
    def shuffled_questions(self):
        qs = self.questions.all()
        if self.shuffle_questions:
            return qs.order_by('?')
        return qs


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'چند گزینه‌ای (تک پاسخ)'),
        ('multiple_answer', 'چند گزینه‌ای (چند پاسخ)'),
        ('true_false', 'صحیح / غلط'),
        ('short_answer', 'پاسخ کوتاه'),
        ('essay', 'توصیفی (تشریحی)'),
        ('matching', 'جورکردنی'),
        ('fill_blank', 'پر کردن جای خالی'),
        ('ordering', 'ترتیب‌دهی'),
    ]

    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='questions', verbose_name="آزمون"
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, verbose_name="نوع سوال"
    )
    title = models.TextField(verbose_name="متن سوال", help_text="متن اصلی سوال را وارد کنید")
    points = models.PositiveIntegerField(default=1, verbose_name="نمره")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    image = models.ImageField(
        upload_to='exam/questions/', blank=True, null=True, verbose_name="تصویر سوال"
    )
    is_required = models.BooleanField(default=True, verbose_name="اجباری")
    explanation = models.TextField(
        blank=True, null=True, verbose_name="توضیح پاسخ",
        help_text="پس از پاسخ، این توضیح به هنرجو نشان داده می‌شود"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.title[:50]}"

    @property
    def shuffled_choices(self):
        qs = self.choices.all()
        if self.exam.shuffle_choices:
            return qs.order_by('?')
        return qs


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='choices', verbose_name="سوال"
    )
    text = models.TextField(verbose_name="متن گزینه")
    image = models.ImageField(
        upload_to='exam/choices/', blank=True, null=True, verbose_name="تصویر گزینه"
    )
    is_correct = models.BooleanField(default=False, verbose_name="گزینه صحیح")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "گزینه"
        verbose_name_plural = "گزینه‌ها"
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:50]


class MatchingPair(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='matching_pairs',
        verbose_name="سوال جورکردنی"
    )
    left_text = models.TextField(verbose_name="متن ستون راست")
    left_image = models.ImageField(
        upload_to='exam/matching/', blank=True, null=True, verbose_name="تصویر ستون راست"
    )
    right_text = models.TextField(verbose_name="متن ستون چپ (پاسخ)")
    right_image = models.ImageField(
        upload_to='exam/matching/', blank=True, null=True, verbose_name="تصویر ستون چپ"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "جفت جورکردنی"
        verbose_name_plural = "جفت‌های جورکردنی"
        ordering = ['order', 'id']


class FillBlankAnswer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='fill_blank_answers',
        verbose_name="سوال جای خالی"
    )
    answer_text = models.TextField(verbose_name="پاسخ صحیح")
    acceptable_alternatives = models.TextField(
        blank=True, null=True, verbose_name="سایر پاسخ‌های قابل قبول",
        help_text="هر پاسخ در یک خط جدا"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="شماره جای خالی")

    class Meta:
        verbose_name = "پاسخ جای خالی"
        verbose_name_plural = "پاسخ‌های جای خالی"
        ordering = ['order', 'id']


class OrderingItem(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='ordering_items',
        verbose_name="سوال ترتیب‌دهی"
    )
    text = models.TextField(verbose_name="متن آیتم")
    image = models.ImageField(
        upload_to='exam/ordering/', blank=True, null=True, verbose_name="تصویر آیتم"
    )
    correct_order = models.PositiveIntegerField(verbose_name="ترتیب صحیح")

    class Meta:
        verbose_name = "آیتم ترتیب‌دهی"
        verbose_name_plural = "آیتم‌های ترتیب‌دهی"
        ordering = ['correct_order']


class ExamAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'در حال انجام'),
        ('submitted', 'ارسال شده'),
        ('graded', 'تصحیح شده'),
    ]

    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='attempts', verbose_name="آزمون"
    )
    student = models.ForeignKey(
        StudentEnrollment, on_delete=models.CASCADE, related_name='exam_attempts',
        verbose_name="هنرجو"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="وضعیت"
    )
    score = models.FloatField(null=True, blank=True, verbose_name="نمره")
    max_score = models.PositiveIntegerField(default=0, verbose_name="حداکثر نمره")
    is_passed = models.BooleanField(default=False, verbose_name="قبول شده")
    attempt_number = models.PositiveIntegerField(default=1, verbose_name="شماره تلاش")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="آی پی")
    user_agent = models.TextField(blank=True, null=True, verbose_name="مرورگر")
    is_cheating_suspected = models.BooleanField(default=False, verbose_name="مشکوک به تقلب")

    class Meta:
        verbose_name = "تلاش آزمون"
        verbose_name_plural = "تلاش‌های آزمون"
        ordering = ['-start_time']
        unique_together = ('exam', 'student', 'attempt_number')

    def __str__(self):
        return f"{self.student} - {self.exam.title} (تلاش {self.attempt_number})"

    @property
    def duration_seconds(self):
        if not self.end_time:
            return (timezone.now() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()

    @property
    def duration_display(self):
        secs = int(self.duration_seconds)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h} ساعت و {m} دقیقه"
        return f"{m} دقیقه و {s} ثانیه"

    @property
    def score_percent(self):
        if self.max_score and self.score is not None:
            return round((self.score / self.max_score) * 100, 1)
        return 0

    @property
    def is_time_up(self):
        if self.status != 'in_progress':
            return False
        elapsed = self.duration_seconds
        max_duration = self.exam.duration_minutes * 60
        return elapsed > max_duration


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(
        ExamAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name="تلاش"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='student_answers', verbose_name="سوال"
    )
    selected_choices = models.ManyToManyField(
        Choice, blank=True, verbose_name="گزینه‌های انتخاب شده"
    )
    text_answer = models.TextField(blank=True, null=True, verbose_name="پاسخ متنی")
    matching_answers = models.JSONField(
        blank=True, null=True, verbose_name="پاسخ‌های جورکردنی",
        help_text='{"left_id": "right_id", ...}'
    )
    fill_blank_answers = models.JSONField(
        blank=True, null=True, verbose_name="پاسخ‌های جای خالی",
        help_text='{"blank_id": "answer_text", ...}'
    )
    ordering_answers = models.JSONField(
        blank=True, null=True, verbose_name="ترتیب قرار داده شده",
        help_text='[item_id, item_id, ...] به ترتیب'
    )
    file_answer = models.FileField(
        upload_to='exam/answers/', blank=True, null=True, verbose_name="فایل پاسخ"
    )
    is_correct = models.BooleanField(null=True, blank=True, verbose_name="صحیح است؟")
    score = models.FloatField(null=True, blank=True, verbose_name="نمره کسب شده")
    graded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='graded_answers', verbose_name="تصحیح شده توسط"
    )
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تصحیح")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پاسخ هنرجو"
        verbose_name_plural = "پاسخ‌های هنرجویان"

    def __str__(self):
        return f"{self.attempt.student} - {self.question.title[:30]}"
