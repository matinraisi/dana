from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django_jalali.db import models as jmodels


national_code_validator = RegexValidator(r'^\d{10}$', 'کد ملی باید ۱۰ رقم باشد.')
phone_validator = RegexValidator(r'^09\d{9}$', 'شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد.')


class SchoolProfile(models.Model):
    """Identity of the one school operated by this isolated installation."""

    name = models.CharField(max_length=255, verbose_name='نام مدرسه')
    education_code = models.CharField(max_length=50, blank=True, verbose_name='کد آموزش و پرورش')
    phone_number = models.CharField(max_length=20, blank=True, verbose_name='تلفن')
    address = models.TextField(blank=True, verbose_name='نشانی')
    logo = models.ImageField(upload_to='school/profile/', blank=True, null=True, verbose_name='لوگو')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مشخصات مدرسه'
        verbose_name_plural = 'مشخصات مدرسه'

    def clean(self):
        if SchoolProfile.objects.exclude(pk=self.pk).exists():
            raise ValidationError('هر نصب مدرسه فقط یک مشخصات مدرسه دارد.')

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    title = models.CharField(max_length=30, unique=True, verbose_name='عنوان سال تحصیلی')
    start_date = jmodels.jDateField(verbose_name='تاریخ شروع')
    end_date = jmodels.jDateField(verbose_name='تاریخ پایان')
    is_active = models.BooleanField(default=False, verbose_name='سال تحصیلی فعال')

    class Meta:
        verbose_name = 'سال تحصیلی'
        verbose_name_plural = 'سال‌های تحصیلی'
        ordering = ['-start_date']

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.'})

    def __str__(self):
        return self.title


class GradeLevel(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name='پایه تحصیلی')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب نمایش')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'پایه تحصیلی'
        verbose_name_plural = 'پایه‌های تحصیلی'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class StudyField(models.Model):
    title = models.CharField(max_length=150, unique=True, verbose_name='رشته تحصیلی')
    code = models.CharField(max_length=30, unique=True, verbose_name='کد رشته')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'رشته تحصیلی'
        verbose_name_plural = 'رشته‌های تحصیلی'
        ordering = ['title']

    def __str__(self):
        return self.title


class Classroom(models.Model):
    class Gender(models.TextChoices):
        GIRLS = 'girls', 'دخترانه'
        BOYS = 'boys', 'پسرانه'
        COED = 'coed', 'مختلط'

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='classrooms', verbose_name='سال تحصیلی')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='classrooms', verbose_name='پایه')
    study_field = models.ForeignKey(StudyField, on_delete=models.PROTECT, related_name='classrooms', null=True, blank=True, verbose_name='رشته')
    title = models.CharField(max_length=100, verbose_name='نام کلاس')
    code = models.CharField(max_length=30, verbose_name='کد کلاس')
    capacity = models.PositiveSmallIntegerField(default=30, verbose_name='ظرفیت')
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.COED, verbose_name='جنسیت')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'کلاس'
        verbose_name_plural = 'کلاس‌ها'
        ordering = ['academic_year__start_date', 'grade_level__order', 'code']
        constraints = [models.UniqueConstraint(fields=['academic_year', 'code'], name='school_unique_classroom_code_per_year')]

    def __str__(self):
        return f'{self.academic_year} - {self.title}'


class Guardian(models.Model):
    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    national_code = models.CharField(max_length=10, unique=True, null=True, blank=True, validators=[national_code_validator], verbose_name='کد ملی')
    mobile_number = models.CharField(max_length=11, unique=True, validators=[phone_validator], verbose_name='شماره موبایل')
    address = models.TextField(blank=True, verbose_name='نشانی')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ولی / سرپرست'
        verbose_name_plural = 'اولیا و سرپرستان'
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.full_name


class Student(models.Model):
    class Gender(models.TextChoices):
        GIRL = 'girl', 'دختر'
        BOY = 'boy', 'پسر'

    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    national_code = models.CharField(max_length=10, unique=True, validators=[national_code_validator], verbose_name='کد ملی')
    birth_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تولد')
    gender = models.CharField(max_length=5, choices=Gender.choices, verbose_name='جنسیت')
    mobile_number = models.CharField(max_length=11, blank=True, validators=[phone_validator], verbose_name='شماره موبایل دانش‌آموز')
    address = models.TextField(blank=True, verbose_name='نشانی')
    photo = models.ImageField(upload_to='school/students/', blank=True, null=True, verbose_name='عکس')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'دانش‌آموز'
        verbose_name_plural = 'دانش‌آموزان'
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.full_name


class StudentGuardian(models.Model):
    class Relationship(models.TextChoices):
        FATHER = 'father', 'پدر'
        MOTHER = 'mother', 'مادر'
        GUARDIAN = 'guardian', 'سرپرست قانونی'
        OTHER = 'other', 'سایر'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardian_links', verbose_name='دانش‌آموز')
    guardian = models.ForeignKey(Guardian, on_delete=models.PROTECT, related_name='student_links', verbose_name='ولی / سرپرست')
    relationship = models.CharField(max_length=10, choices=Relationship.choices, verbose_name='نسبت')
    is_primary = models.BooleanField(default=False, verbose_name='ولی اصلی')
    receives_notifications = models.BooleanField(default=True, verbose_name='دریافت‌کننده اعلان‌ها')

    class Meta:
        verbose_name = 'ارتباط دانش‌آموز و ولی'
        verbose_name_plural = 'ارتباط دانش‌آموزان و اولیا'
        constraints = [models.UniqueConstraint(fields=['student', 'guardian'], name='school_unique_student_guardian')]

    def clean(self):
        if self.is_primary and StudentGuardian.objects.filter(student=self.student, is_primary=True).exclude(pk=self.pk).exists():
            raise ValidationError({'is_primary': 'برای هر دانش‌آموز فقط یک ولی اصلی مجاز است.'})

    def __str__(self):
        return f'{self.student} - {self.guardian}'


class SchoolEnrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'فعال'
        TRANSFERRED = 'transferred', 'منتقل شده'
        GRADUATED = 'graduated', 'فارغ‌التحصیل'
        WITHDRAWN = 'withdrawn', 'انصراف داده'

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='school_enrollments', verbose_name='دانش‌آموز')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='enrollments', verbose_name='سال تحصیلی')
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name='enrollments', verbose_name='کلاس')
    student_number = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name='شماره دانش‌آموزی')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE, verbose_name='وضعیت')
    enrolled_at = jmodels.jDateField(verbose_name='تاریخ ثبت‌نام')
    note = models.TextField(blank=True, verbose_name='یادداشت')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ثبت‌نام تحصیلی'
        verbose_name_plural = 'ثبت‌نام‌های تحصیلی'
        ordering = ['-academic_year__start_date', 'student__last_name']
        constraints = [models.UniqueConstraint(fields=['student', 'academic_year'], name='school_unique_student_enrollment_per_year')]

    def clean(self):
        if self.classroom_id and self.academic_year_id and self.classroom.academic_year_id != self.academic_year_id:
            raise ValidationError({'classroom': 'کلاس انتخاب‌شده متعلق به سال تحصیلی انتخاب‌شده نیست.'})

    def __str__(self):
        return f'{self.student} - {self.academic_year}'
