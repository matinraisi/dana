# Dana (دانا) — Education Platform

## خلاصه پروژه
دانا یک **Education Platform** تک‌کدبیس است با سه پروفایل نصب (`PRODUCT_MODE` در `install_config.py`):

| Mode | نقش |
|---|---|
| `academy` | نصب مشتری برای آموزشگاه |
| `school` | نصب مشتری برای مدرسه (K-12) |
| `control` | پنل داخلی دانا (فروش، مشتری، لایسنس) — نه tenant مشتری |

قرارداد معماری: [`docs/architecture-contract.md`](docs/architecture-contract.md)

**Tenancy تجاری:** هر مشتری = یک Instance جدا (DB / دامنه / media / settings).  
داخل Academy Instance دقیقاً **یک سازمان** (`schools.School` singleton) — بدون subdomain و بدون `SchoolMiddleware` / `SchoolFilterMixin`.  
سوئیچ پروفایل: `install_config.py` → `config/profile.py` (نه `.env` و نه branching پراکنده در منطق دامنه).

## استک فناوری
- **Backend:** Django 6.0 + Python 3.10-3.12
- **Frontend:** Tailwind CSS v4 (django-tailwind) + قالب‌های Django + PWA shell
- **دیتابیس:** SQLite (لوکال) / MySQL (هاست) — یک DB per instance
- **پیامک:** IPPanel (`apps.notifications.sms`)
- **پرداخت:** آقای پرداخت مستقیم، یا درگاه سان‌تک وقتی env پر باشد
- **کلاس آنلاین:** Jitsi Meet
- **تقویم:** django-jalali
- **فایل‌ها:** Whitenoise + Pillow
- **احراز هویت:** OTP + رمز عبور (بر اساس نقش/پروفایل)

## هویت برند (پیش‌فرض دانا)
- **نام:** دانا (Dana)
- **زیرعنوان:** پلتفرم مدیریت هوشمند آموزش
- **رنگ‌ها:** بنفش (purple-*) + سفید
- **تلفن:** ۰۹۱۵۶۳۰۸۲۳۰
- برندینگ هر Instance از `InstallationConfig` خوانده می‌شود

## ساختار پروژه
```
├── apps/
│   ├── academy/            ← پروفایل آموزشگاه (دوره، هنرجو، مالی، آزمون، پیامک، …)
│   ├── school_management/  ← پروفایل مدرسه (سال تحصیلی، پایه، کلاس، دانش‌آموز، ولی)
│   ├── control_center/     ← پروفایل کنترل (درخواست‌ها، مشتری، لایسنس، نصب)
│   ├── users/              ← User + OTP + نقش‌ها
│   ├── installation/       ← برندینگ/تنظیمات singleton هر Instance
│   ├── notifications/      ← ارسال SMS سطح پایین (IPPanel)
│   ├── schools/            ← Academy Org (legacy؛ یک org per instance)
│   ├── crm/                ← CRM آموزشگاه
│   ├── teacher_panel/      ← پنل استاد
│   ├── student_panel/      ← پنل هنرجو
│   └── forms_builder/      ← فرم‌ساز
├── config/                 ← settings + profile.py + urls
├── theme/                  ← قالب‌ها + Tailwind + PWA assets
├── website/                ← لندینگ/وب‌سایت (اختیاری با WEBSITE_ENABLED)
├── docs/                   ← قرارداد معماری (architecture-contract.md منبع حقیقت)
├── scripts/                ← init / verify_profile_schemas
├── deploy/                 ← entrypoint
├── manage.py
├── Dockerfile
└── AGENTS.md
```

## Shared kernel (محدود)
`users`, `installation`, `notifications`, الگوهای پرداخت، theme/PWA، ابزار deploy.  
مدل‌های Student/Course/Enrollment بین Academy و School مشترک **نیستند**.

## نقش‌ها
### Academy
| نقش | پنل |
|---|---|
| سوپریوزر / مدیر آموزشگاه | `/dashboard/` |
| استاد | `/teacher/` |
| هنرجو | `/my/` |

### School
| نقش | پنل |
|---|---|
| مدیر مدرسه / staff | `/admin/` و `/school-panel/` |
| نقش‌های `SCHOOL_*` | برای رشد بعدی پروفایل مدرسه |

### Control
| نقش | پنل |
|---|---|
| سوپریوزر دانا | `/control/` + `/admin/` |

## URL بر اساس PRODUCT_MODE
### academy
```
/                       ← لندینگ (اگر WEBSITE_ENABLED)
/dashboard/             ← پنل ادمین
/teacher/               ← پنل استاد
/my/                    ← پنل هنرجو
/crm/                   ← CRM
/forms/                 ← فرم‌ساز
/auth/                  ← OTP / رمز
/register/<slug>/       ← ثبت‌نام عمومی دوره
/pay/<id>/              ← پرداخت عمومی
/payment/gateway/...    ← webhook/return درگاه سان‌تک
/verify/<card>/         ← تأیید کارت
```

### school
```
/admin/                 ← Django admin مدرسه
/school-panel/          ← پنل مدرسه (vertical اول)
```

### control
```
/control/request/       ← فرم درخواست عمومی
/control/requests/      ← لیست درخواست‌ها
/control/customers/     ← مشتریان
/control/licenses/      ← لایسنس‌ها
/admin/                 ← Django admin
```

## پرداخت (Academy)
- ورودی مشترک: `apps.academy.services.payment_flow.start_online_payment`
- اگر `PAYMENT_GATEWAY_*` پر باشد → درگاه سان‌تک + webhook امضاشده
- وگرنه → آقای پرداخت + `PaymentCallbackView`
- settle فقط از `settle_success` / `settle_failure` (idempotent)
- تست: `python manage.py test apps.academy.tests_gateway`

## پیامک
- فقط IPPanel از طریق `apps.notifications.sms.send_sms`
- لاگ محصولی Academy در `SMSLog`؛ Control لاگ academy ندارد

## ماژول‌ها
| ماژول | سیاست |
|---|---|
| Panel + PWA | همیشه برای Instance مشتری |
| Website | اختیاری (`WEBSITE_ENABLED`) |
| AI | فعلاً نه |
| Auto-provisioning | فعلاً نه؛ Control دستی |

## امنیت و مرز نقش‌ها
- مالکیت روی پروفایل/کارت هنرجو؛ Forms builder با `created_by`
- فرم عمومی: فقط `is_active` و `is_public`
- CSRF روی فرم‌ها و AJAX پیامک
- استاد/هنرجو به داشبورد ادمین، CRM، SMS ادمین، و Forms ادمین دسترسی ندارند (403)
- اعتبارسنجی آپلود (MIME + ۵MB)
- رمز پیش‌فرض نباید در production باقی بماند

## تست‌های معماری
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test config.tests_profile_isolation apps.users.tests_kernel_purity apps.schools.tests_singleton apps.academy.tests_gateway
python scripts/verify_profile_schemas.py
```

Full system regression checkpoint (STEP 21): **172 PASS / 0 FAIL / 2 SKIP**.  
Deferred / non-blocking warnings: [`docs/architecture-contract.md`](docs/architecture-contract.md) → *Known limitations / deferred*.

## استقرار Instance
`PRODUCT_MODE` باید صریحاً در `install_config.py` تنظیم شود (`academy` | `school` | `control`) — نه در `.env`، بدون پیش‌فرض خاموش به academy.

اولین نصب مشتری: [`docs/customer-first-install.md`](docs/customer-first-install.md)  
(`install_config.py` → `migrate` → `createsuperuser` → InstallationConfig → Academy: `init_academy_org.py --title "..."` / School: SchoolProfile)

```bash
# install_config.py (از install_config.example.py)
PRODUCT_MODE = "academy"   # یا "school" / "control"
WEBSITE_ENABLED = False

# .env نمونه (از .env.example) — فقط secrets/infra
DEBUG=False
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=customer.example.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://customer.example.com
IPPANEL_API_TOKEN=...
IPPANEL_SENDER=...
```

راهنمای ارتقا: [`docs/instance-upgrade.md`](docs/instance-upgrade.md)

## نکات فنی
- CSS لوکال: `{% static 'css/dist/styles.css' %}`
- فونت Vazirmatn لوکال
- هویت نصب جدا: `DANA_INSTALL_FILE=...`؛ secrets جدا: `DANA_ENV_FILE=.env.school`
- رنگ برندینگ Instance از `installation.primary_color` (CSS variables)
- Website landing: `website/cademy.html`؛ CTA عمومی از `Profile.website_public_context` (نه hard-code مسیر Academy)
- Hosting / demo map (قفل): [`docs/hosting-and-demo.md`](docs/hosting-and-demo.md) — سایت مرکزی `edu-aihousesb.ir`، دموهای جدا، نصب مشتری؛ بدون ادغام پروفایل‌ها
- اسناد مرجع: `docs/architecture-contract.md`, `docs/customer-first-install.md`, `docs/hosting-and-demo.md`, `docs/school-core-architecture.md`, `docs/installation.md`, `docs/instance-upgrade.md`, `docs/website-module.md`
