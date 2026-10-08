# دانا (Dana) — لیست مشکلات و بهبودها

> اولویت‌بندی بر اساس بخش و فوریت. هر آیتم قابل رد کردن (check) است.  
> قرارداد معماری: [`docs/architecture-contract.md`](docs/architecture-contract.md)

---

## 🔴 P0 — فوری (امنیت / بحرانی)

- [ ] **ISS-001:** فایل `.env` حاوی SECRET_KEY و KAVENEGAR_API_KEY در git ذخیره شده — باید rotate شود
- [x] **ISS-002:** `mark_safe()` در admin اکسل/SMS — به قالب امن منتقل شد ✅
- [x] **ISS-003:** Bare `except:` در admin — به `except Exception` + مسیر امن ✅
- [x] **ISS-004:** OTP بدون rate limiting در `users/views.py` — امکان brute-force ✅
- [x] **ISS-005:** `private_storage` از settings حذف شد (وابستگی نبود) ✅

---

## 🟡 P1 — مهم (معماری / کیفیت کد)

### بخش لاگین و احراز هویت
- [x] **ISS-006:** `OTPRequestView.post()` بدون validation امنیتی کافی — نیاز به captcha یا rate limit ✅ rate limiting اضافه شد
- [x] **ISS-007:** `OTPVerifyView` بعد از verify پاک نمی‌شود اگر کاربر back بزند — session reuse ✅ کامل پاکسازی session
- [x] **ISS-008:** `AcademyLoginView` lockout بعد از ۵ تلاش ✅
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
- [x] **ISS-029:** CRM views با AdminRequiredMixin + school_object_or_404 (single-org) ✅
- [ ] **ISS-030:** `LeadActivity` بدون rate limit — امکان spam

---

## 🟢 P2 — بهبود (Performance / Cleanup)

### عملکرد
- [ ] **ISS-031:** `DashboardHomeView` چندین query جداگانه — باید `select_related` استفاده شود
- [ ] **ISS-032:** `Teacher.total_earnings` property — N+1 query در هر بار فراخوانی
- [ ] **ISS-033:** `Teacher.total_sessions` property — N+1 query
- [ ] **ISS-034:** `TeacherExamResultsView.get_stats()` loop روی queryset — باید aggregate شود

### تمیزکاری کد
- [x] **ISS-035:** اپلیکیشن‌های مرده: `apps/core/`, `apps/accounting/` — حذف شدند ✅
- [x] **ISS-035b:** `SchoolMiddleware` / register multi-tenant schools / `admin_base` — حذف از استک فعال ✅
- [ ] **ISS-036:** `import timezone` تکراری در `teacher_panel/views.py:6,13`
- [ ] **ISS-037:** `unique_together` منسوخ → `UniqueConstraint`
- [ ] **ISS-038:** `admin.py` بیش از ۶۰۰ خط → split به فایل‌های جداگانه
- [ ] **ISS-039:** `related_name='active_enrollments'` روی `CourseEnrollment` — در dashboard از `enrollments` استفاده شده (potential mismatch)
- [ ] **ISS-040:** Magic number `300` در OTP validity → constant
- [ ] **ISS-040b:** یکپارچه‌سازی mountهای تکراری URL عمومی Academy (`/register` vs `/dashboard/register`, `/pay` vs nested)

### تست
- [x] **ISS-041:** تست‌های معماری فعال: profile isolation، kernel purity، singleton org، gateway ✅
- [ ] **ISS-042:** `tests.py` خالی در اکثر اپلیکیشن‌های محصولی (CRM/Forms/…) — پوشش رفتاری هنوز کم است
---

## 🔵 P3 — آینده (Features / Enhancements)

- [ ] **ISS-043:** Celery Beat برای کارهای دوره‌ای (بروزرسانی status overdue)
- [ ] **ISS-044:** Logging ساختاریافته با فرمت JSON
- [ ] **ISS-045:** API (DRF) برای موبایل
- [ ] **ISS-046:** Soft delete برای حذف رکوردها
- [ ] **ISS-047:** Caching برای query‌های سنگین dashboard

---

## 📋 QA پروفایل Academy (پس از Phase 3)

| بلوک | نتیجه | یادداشت |
|---|---|---|
| Auth / Core Admin / Teacher / Student | PASS | materials: `{% load custom_filters %}` |
| Public registration | PASS پس از fix | nested pay: `slug=None` |
| CRM | PASS | بدون delete route |
| Forms Builder | PASS پس از fix | `is_public` در public view |
| SMS / Notifications | PASS پس از fix | import `Q` برای search |
| Control 403 template | PASS پس از fix | مسیر فونت استاتیک |

---

## 📋 Architecture checkpoint (STEP 21 + docs)

| مورد | وضعیت |
|---|---|
| Full system regression | **172 PASS / 0 FAIL / 2 SKIP** |
| Cross-profile isolation | PASS |
| Website profile CTAs | PASS (hooks در `config/profile.py`) |
| قالب مرده `website/home.html` | حذف شد (unmounted؛ `HomeView` → `cademy.html`) |

### Deferred / non-blocking (ثبت در contract)

- [ ] Mount تکراری register/pay/verify (ISS-040b)
- [ ] `/dashboard/my/exams/` به‌جای مسیر `/my/`
- [ ] یک لینک GET logout در `teacher/base.html` (LogoutView = POST)
- [ ] نام‌گذاری `apps.schools` = Academy Org (نه School Product)
- [ ] School: بدون attendance/exams/finance/پنل دبیر
- [ ] Control: بدون dashboard/settings محصولی؛ update درخواست POST-only
- [ ] templates.W003 duplicate `custom_filters` (theme + academy)
- [ ] محدودیت فضای دیسک C: روی ماشین توسعه (ENVIRONMENT)

---

## 📋 Fresh Academy install (2026-10-08)

| مورد | وضعیت |
|---|---|
| Empty DB `migrate` + `createsuperuser` + `/dashboard/` | PASS با مراحل دستی |
| هویت محصول | `install_config.py` (`PRODUCT_MODE` / `WEBSITE_ENABLED`)، نه `.env` |
| CSS | بدون `tailwind build` + `collectstatic` لاگین با manifest error می‌شکند |
| برندینگ Academy | عنوان فقط با `init_academy_org.py`؛ `/admin/` روی Academy نیست؛ فرم داشبورد سازمان هنوز نیست |

- [ ] **ISS-048:** صفحهٔ مشخصات سازمان در داشبورد Academy (نام، لوگو، تلفن، ایمیل، نشانی، رنگ) — بدون Django Admin و بدون ویزارد جدید

---

## 📋 تاریخچه اجرا

| تاریخ | آیتم | وضعیت |
|---|---|---|
| 2026-10-08 | Fresh Academy install audit | ✅ PASS WITH MANUAL STEPS؛ docs هم‌راستا شد؛ ISS-048 باز |
| 2026-10-07 | Architecture checkpoint | ✅ docs sync + حذف `website/home.html`؛ QA 172/0/2 |
| 2026-10-06 | ISS-035 / tenancy cleanup | ✅ حذف core/accounting + middleware tenancy؛ docs sync |
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
