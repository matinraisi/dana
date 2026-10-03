# Cademy — لیست مشکلات و بهبودها

> اولویت‌بندی بر اساس بخش و فوریت. هر آیتم قابل رد کردن (check) است.

---

## 🔴 P0 — فوری (امنیت / بحرانی)

- [ ] **ISS-001:** فایل `.env` حاوی SECRET_KEY و KAVENEGAR_API_KEY در git ذخیره شده — باید rotate شود
- [ ] **ISS-002:** `mark_safe()` در `admin.py:230,294` روی HTML داینامیک — XSS potential
- [ ] **ISS-003:** Bare `except:` در `admin.py:220,325,664` — بلعیدن تمام exceptionها بدون لاگ
- [x] **ISS-004:** OTP بدون rate limiting در `users/views.py` — امکان brute-force ✅
- [ ] **ISS-005:** `private_storage` در settings تعریف شده ولی در requirements.txt نیست — خطای احتمالی

---

## 🟡 P1 — مهم (معماری / کیفیت کد)

### بخش لاگین و احراز هویت
- [x] **ISS-006:** `OTPRequestView.post()` بدون validation امنیتی کافی — نیاز به captcha یا rate limit ✅ rate limiting اضافه شد
- [x] **ISS-007:** `OTPVerifyView` بعد از verify پاک نمی‌شود اگر کاربر back بزند — session reuse ✅ کامل پاکسازی session
- [ ] **ISS-008:** `AcademyLoginView` فقط username/password — بدون lockout بعد از N تلاش ناموفق
- [x] **ISS-009:** `TeacherRequiredMixin` و `StudentRequiredMixin` تقریباً identical — باید abstract شوند ✅ `RoleRequiredMixin` اضافه شد

### بخش SMS
- [ ] **ISS-010:** سه کد تکراری ارسال SMS: `services/sms_service.py`, `utils.py`, `admin.py`
- [ ] **ISS-011:** `bulk_send()` در sms_service.py به صورت loop ساده — بدون parallel یا rate limit
- [ ] **ISS-012:** ثبت SMSLog حتی اگر send ناموفق باشد `is_sent=False` — log بزرگ می‌شود

### بخش مالی و پرداخت
- [ ] **ISS-013:** `PaymentCallbackView` بدون CSRF — callback از درگاه POST نمی‌شود (GET) ولی verify ندارد
- [ ] **ISS-014:** `RecordPaymentView` بدون double-submit prevention — ممکن است پرداخت تکراری ثبت شود
- [ ] **ISS-015:** `FinanceDashboardView` query سنگین بدون pagination
- [ ] **ISS-016:** `AcademyInstallment` update در هر GET request — باید celery task باشد

### بخش هنرجو
- [ ] **ISS-017:** `StudentCreateView.post()` بدون Django Form — raw POST data
- [ ] **ISS-018:** `StudentEditView.post()` action handling پیچیده و سخت تست — باید split شود
- [ ] **ISS-019:** `_ensure_student_user()` helper تعریف شده ولی در `public_registration.py` تکرار شده
- [ ] **ISS-020:** `StudentDeleteView` بدون soft delete — حذف فیزیکی خطرناک
- [ ] **ISS-021:** `ImportExcelView` بدون error handling کافی — یک سطر خراب کل فایل را خراب نکند
- [ ] **ISS-022:** `StudentEnrollment.save()` loop برای تولید short_slug — race condition

### بخش دوره
- [ ] **ISS-023:** `Course.save()` فقط status FULL را چک می‌کند — نه auto-complete
- [ ] **ISS-024:** `Session.generate_jitsi_link()` از MD5 hash — امنیتی نیست ولی قابل حدس نیست (acceptable)
- [ ] **ISS-025:** `CourseEnrollment.update_paid_amount()` از Python loop به جای ORM aggregate

### بخش آزمون
- [ ] **ISS-026:** `TakeExamView` timeout فقط client-side — بدون server-side validation
- [ ] **ISS-027:** `ExamAttempt.is_time_up` property در هر بار فراخوانی محاسبه می‌شود — باید cached باشد
- [ ] **ISS-028:** `auto_grade_attempt()` بعد از grading تشریحی — باید atomic باشد

### بخش CRM
- [ ] **ISS-029:** `Lead` model بدون school filter در views — احتمال leak بین مدارس
- [ ] **ISS-030:** `LeadActivity` بدون rate limit — امکان spam

---

## 🟢 P2 — بهبود (Performance / Cleanup)

### عملکرد
- [ ] **ISS-031:** `DashboardHomeView` چندین query جداگانه — باید `select_related` استفاده شود
- [ ] **ISS-032:** `Teacher.total_earnings` property — N+1 query در هر بار فراخوانی
- [ ] **ISS-033:** `Teacher.total_sessions` property — N+1 query
- [ ] **ISS-034:** `TeacherExamResultsView.get_stats()` loop روی queryset — باید aggregate شود

### تمیزکاری کد
- [ ] **ISS-035:** اپلیکیشن‌های مرده: `apps/core/`, `apps/accounting/` — حذف شوند
- [ ] **ISS-036:** `import timezone` تکراری در `teacher_panel/views.py:6,13`
- [ ] **ISS-037:** `unique_together` منسوخ → `UniqueConstraint`
- [ ] **ISS-038:** `admin.py` بیش از ۶۰۰ خط → split به فایل‌های جداگانه
- [ ] **ISS-039:** `related_name='active_enrollments'` روی `CourseEnrollment` — در dashboard از `enrollments` استفاده شده (potential mismatch)
- [ ] **ISS-040:** Magic number `300` در OTP validity → constant

### تست
- [ ] **ISS-041:** صفر تست فعال در پروژه — حداقل برای بخش‌های حیاتی
- [ ] **ISS-042:** `tests.py` خالی در اکثر اپلیکیشن‌ها

---

## 🔵 P3 — آینده (Features / Enhancements)

- [ ] **ISS-043:** Celery Beat برای کارهای دوره‌ای (بروزرسانی status overdue)
- [ ] **ISS-044:** Logging ساختاریافته با فرمت JSON
- [ ] **ISS-045:** API (DRF) برای موبایل
- [ ] **ISS-046:** Soft delete برای حذف رکوردها
- [ ] **ISS-047:** Caching برای query‌های سنگین dashboard

---

## 📋 تاریخچه اجرا

| تاریخ | آیتم | وضعیت |
|---|---|---|
| 2026-07-12 | ISS-004 | ✅ rate limiting اضافه شد (60s cooldown + 10/hour limit) |
| 2026-07-12 | ISS-006 | ✅ rate limiting در OTPRequestView و OTPResendView |
| 2026-07-12 | ISS-007 | ✅ پاکسازی کامل session بعد از login موفق |
| 2026-07-12 | ISS-008 | ✅ Admin login lockout بعد از ۵ بار اشتباه |
| 2026-07-12 | ISS-009 | ✅ `RoleRequiredMixin` در users/mixins.py اضافه شد |
| 2026-07-12 | W1 | ✅ پیامک ثبت‌نام آموزشگاه به 09010208230 |
| 2026-07-12 | W2 | ✅ ورود با رمز عبور برای استاد/هنرجو (tab switcher) |
| 2026-07-12 | W3 | ✅ حذف دکمه جلسه آنلاین از صفحه لاگین مدیر |
| 2026-07-12 | W4 | ✅ بازطراحی UI/UX تمام صفحات لاگین (تم بنفش یکپارچه + glass morphism + animations) |
| 2026-07-12 | MISC | ✅ Management command برای تنظیم رمز پیش‌فرض کاربران موجود |
