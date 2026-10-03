# Cademy (دانا) — پلتفرم اتوماسیون هوشمند آموزشگاه مبتنی بر هوش مصنوعی

## خلاصه پروژه
Cademy (دانا) یک پلتفرم اتوماسیون هوشمند آموزشگاه چندمستاجری با رابط کاربری فارسی است. هر آموزشگاه پنل مدیریت جداگانه دارد و فقط به اطلاعات خودش دسترسی دارد. سوپریوزر به همه مدارس دسترسی دارد.

## استک فناوری
- **Backend:** Django 6.0 + Python 3.10-3.12
- **Frontend:** Tailwind CSS v4 (django-tailwind) + قالب‌های Django
- **دیتابیس:** SQLite (لوکال) / MySQL (هاست cPanel)
- **پیامک:** Kavenegar API
- **پرداخت:** درگاه آقای پرداخت (AqayePardakht) — callback_method=GET
- **کلاس آنلاین:** Jitsi Meet
- **تقویم:** django-jalali (تاریخ شمسی)
- **فایل‌ها:** Whitenoise + Pillow
- **احراز هویت:** OTP (اساتید/هنرجویان) + رمز عبور (مدیران)

## هویت برند
- **نام:** دانا (Dana)
- **زیرعنوان:** پلتفرم اتوماسیون هوشمند آموزشگاه مبتنی بر هوش مصنوعی
- **رنگ‌ها:** بنفش (purple-500 تا purple-900) + سفید
- **تلفن:** ۰۹۱۵۶۳۰۸۲۳۰

## ساختار پروژه
```
cademy/
├── apps/
│   ├── academy/          ← هسته اصلی (دوره‌ها، دانشجویان، امتحانات، مالی، پیامک، حضورغیاب)
│   ├── users/             ← مدل User سفارشی + OTP + استاد/هنرجو
│   ├── crm/               ← مدیریت لیدها و تبدیل به دانشجو (+ فیلد school)
│   ├── teacher_panel/     ← پنل استاد
│   ├── student_panel/     ← پنل هنرجو
│   ├── forms_builder/     ← فرم‌ساز پویا (عمومی)
│   ├── schools/           ← مدل مدرسه + Middleware چندمستاجری
│   ├── core/              ← ❌ کد مرده
│   └── accounting/        ← ❌ کد مرده
├── config/                ← تنظیمات Django
├── theme/                 ← قالب‌ها + Tailwind CSS + static files
├── website/               ← لندینگ دانا
├── static/                ← فایل‌های استاتیک
├── media/                 ← فایل‌های آپلود شده
├── staticfiles/           ← فایل‌های جمع‌آوری شده
├── manage.py
├── passenger_wsgi.py      ← ورودی هاست cPanel
├── requirements.txt
├── .env                   ← تنظیمات محیطی (⚠️ در git نباشد)
├── .gitignore
└── AGENTS.md              ← همین فایل
```

## نقش‌های کاربری
| نقش | دسترسی | پنل |
|---|---|---|
| سوپریوزر | همه مدارس + همه داده‌ها | `/dashboard/` |
| مدیر آموزشگاه | فقط مدرسه خودش | `/dashboard/` |
| استاد | دوره‌ها و دانشجویان خودش | `/teacher/` |
| هنرجو | فقط اطلاعات خودش | `/my/` |
| مهمان | ثبت‌نام عمومی + ورود | `/register/`, `/auth/` |

## ساختار URL
```
/                       ← لندینگ دانا (redirect خودکار کاربران لاگین‌شده)
/dashboard/             ← پنل مدیریت ادمین
/dashboard/login/       ← لاگین مدیر
/teacher/               ← پنل استاد
/my/                    ← پنل هنرجو
/crm/                   ← CRM
/auth/teacher/login/    ← لاگین استاد (OTP)
/auth/student/login/    ← لاگین هنرجو (OTP)
/school/register/       ← ثبت‌نام مدرسه جدید
/register/<slug>/       ← ثبت‌نام عمومی دوره
/pay/<id>/              ← پرداخت عمومی (سطح روت، نه /dashboard/)
/verify/<card_number>/  ← تأیید کارت شناسایی
```

## قابلیت‌های اصلی
- **اتوماسیون هوشمند:** پیامک خودکار (خوش‌آمد، یادآوری، غیبت)
- **مدیریت دوره‌ها و جلسات** (تکرار خودکار هفتگی)
- **سیستم امتحان** (۸ نوع سوال + نمره‌دهی خودکار)
- **حضورغیاب** هوشمند
- **پرداخت آنلاین** (آقای پرداخت) + اقساط + پرداخت عمومی
- **پیامک انبوه** (Kavenegar) + AJAX ارسال با لودینگ + فیلتر (اساتید، هنرجویان، سرنخ‌ها)
- **CRM** (تبدیل لید به دانشجو)
- **فرم‌ساز عمومی**
- **کلاس آنلاین** (Jitsi)
- **برنامه کلاس‌ها** (تقویم هفتگی + نمای فضاها)
- **کارت شناسایی** با QR code
- **گزارش‌های مالی و حسابداری**
- **پنل استاد** (درآمد، پروفایل، قرارداد، شماره کارت/شبا)
- **لندینگ دانا** (صفحه اصلی با تم بنفش + هوش مصنوعی)

## مسیر رشد (لندینگ)
۵ مرحله افقی:
1. ثبت و راه‌اندازی → ۲. ساختارسازی → ۳. جذب هنرجو → ۴. مدیریت روزانه → ۵. رشد هوشمند

## امنیت (audit اعمال شده)
- **SEC-1:** `LoginRequiredMixin` + بررسی مالکیت روی `StudentProfileView` و `StudentIdCardView`
- **SEC-2:** `PublicPaymentInitiateView` با POST + جلوگیری از تراکنش تکراری
- **SEC-3:** اعتبارسنجی فایل آپلودی (MIME type + حداکثر ۵ مگابایت)
- **SEC-4:** `SchoolFilterMixin` روی تمام ویوهای ادمین
- **SEC-5:** `school_object_or_404` helper برای `get_object_or_404` با فیلتر مدرسه
- CSRF protection روی تمام فرم‌ها
- `CSRF_COOKIE_SECURE` = `default=not DEBUG`
- Whitenoise برای سرو فایل‌های استاتیک

## URL ساختار
- `/` → لندینگ (redirect خودکار کاربران لاگین‌شده)
- `/dashboard/` → پنل ادمین (تمام URLهای academy)
- `/teacher/` → پنل استاد
- `/my/` → پنل هنرجو
- `/pay/<id>/` → پرداخت عمومی (سطح روت، نه /dashboard/)

## پرداخت (آقای پرداخت، از طریق درگاه سان‌تک)
- همهٔ ویوهای پرداخت از `services/payment_flow.start_online_payment` استفاده می‌کنند.
  - اگر `PAYMENT_GATEWAY_URL` / `PAYMENT_GATEWAY_CLIENT_ID` / `PAYMENT_GATEWAY_SECRET` پر باشد،
    پرداخت از **درگاه سان‌تک** (`pay.sbsuntech.ir`، مخزن `payment-gateway`) ساخته می‌شود؛ درگاه
    callback بانک را وریفای می‌کند و نتیجه را با webhook امضاشده به
    `/payment/gateway/webhook/` می‌فرستد. هنرجو به `/payment/gateway/return/` برمی‌گردد.
  - اگر خالی باشد، روش قبلی: مستقیم با آقای پرداخت و `PaymentCallbackView`.
- ثبت نتیجه فقط از `settle_success` / `settle_failure` — موفقیت فقط **یک بار** ثبت می‌شود
  (قفل ردیف)، چون webhook و صفحهٔ بازگشت ممکن است هر دو برسند.
- `paid` بعد از `failed` هنوز ثبت می‌شود (قرارداد درگاه)؛ `failed` بعد از `paid` نادیده گرفته می‌شود.
- تست‌ها: `python manage.py test apps.academy.tests_gateway`

## فایل‌های موردنیاز برای آپلود
```
apps/                    ← تمام کدهای پایتون
config/                  ← تنظیمات
theme/                   ← قالب‌ها + static (شامل CSS کامپایل شده)
static/                  ← فایل‌های استاتیک
media/                   ← (اختیاری)
website/                 ← لندینگ
manage.py
passenger_wsgi.py
requirements.txt
.env                     ← با STATIC_ROOT و MEDIA_ROOT هاست
.gitignore
AGENTS.md
```

## ملاحظات استقرار (cPanel)
```bash
# .env روی هاست:
DEBUG=False
STATIC_ROOT=/home/bahuloun/panel.aihousesb.ir/static/
MEDIA_ROOT=/home/bahuloun/panel.aihousesb.ir/media/
SECRET_KEY=<key_jadid>
ALLOWED_HOSTS=panel.aihousesb.ir,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://panel.aihousesb.ir

# مراحل:
python manage.py migrate
touch passenger_wsgi.py
```

## مایگریشن‌های اخیر
- `academy.0021_session_location` — فیلد محل برگزاری جلسه
- `crm.0002_lead_school` — فیلد مدرسه روی لید CRM
- `users.0005_teacher_card_number_teacher_shaba_number` — شماره کارت و شبا استاد

## نکات فنی مهم
- **CSS:** از فایل لوکال `{% static 'css/dist/styles.css' %}` استفاده شود (نه CDN)
- **فونت:** Vazirmatn از فایل لوکال (نه Google Fonts CDN)
- **رنگ‌ها:** فقط رنگ‌های استاندارد Tailwind (purple-*) — رنگ‌های سفارشی کامپایل نمیشن
- **لندینگ:** `{% load tailwind_tags %}` + `{% tailwind_css %}` الزامی
- **Redirect لاگین:** HomeView کاربران لاگین‌شده رو به پنل خودشون ریدایرکت می‌کنه
