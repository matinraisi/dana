# دانا (Dana) — Education Platform

<p dir="rtl">

پلتفرم مدیریت آموزش با یک codebase و سه پروفایل نصب: آموزشگاه، مدرسه، و کنترل مرکزی.
هر مشتری یک Instance مستقل (دیتابیس، دامنه، media، تنظیمات) دریافت می‌کند.

</p>

---

## قرارداد معماری

منبع حقیقت: [`docs/architecture-contract.md`](docs/architecture-contract.md)

| مفهوم | معنی |
|---|---|
| یک محصول | Education Platform |
| دو پروفایل مشتری | `academy` / `school` |
| پروفایل داخلی | `control` |
| Tenancy | یک مشتری = یک Instance = یک DB |
| Website | اختیاری (`WEBSITE_ENABLED`) |
| PWA | همیشه برای پنل مشتری |

---

## استک

| لایه | فناوری |
|---|---|
| Backend | Django 6.0 + Python 3.10–3.12 |
| Frontend | Tailwind CSS v4 + قالب Django + PWA |
| DB | SQLite (لوکال) / MySQL (هاست) |
| پیامک | IPPanel |
| پرداخت | آقای پرداخت ± درگاه سان‌تک |
| تقویم | django-jalali |

---

## ساختار

```
apps/
  academy/             آموزشگاه (+ CRM/forms/teacher/student panels)
  schools/             سازمان آموزشگاه (singleton per Academy instance)
  school_management/   مدرسه (K-12)
  control_center/      کنترل دانا
  installation/        برندینگ Instance
  notifications/       SMS transport (IPPanel)
  users/
config/                install_config.py → PRODUCT_MODE → profile.py
theme/ website/ docs/ scripts/ deploy/
```

---

## راه‌اندازی لوکال / اولین نصب مشتری

راهنمای کامل: [`docs/customer-first-install.md`](./docs/customer-first-install.md)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp install_config.example.py install_config.py
# Set PRODUCT_MODE = "academy" | "school" | "control" and WEBSITE_ENABLED in install_config.py
cp .env.example .env
# REQUIRED in .env: SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS (no PRODUCT_MODE)
python manage.py migrate
python manage.py createsuperuser
python manage.py tailwind build
python manage.py runserver
```

Academy org (after superuser; real customer name only):

```bash
python scripts/init_academy_org.py --title "Customer Academy Name"
```

School: after login, save SchoolProfile at `/school-panel/profile/` before handover.

پروفایل/secrets جدا روی یک checkout:

```bash
set DANA_INSTALL_FILE=D:\path\to\install_school.py
set DANA_ENV_FILE=.env.school
python manage.py runserver
```

---

## پروفایل‌ها

### Academy (`/dashboard/`, `/teacher/`, `/my/`, `/register/`, `/pay/`)
دوره، هنرجو، مالی، اقساط، آزمون، پیامک، CRM، فرم‌ساز، کارت شناسایی، پرداخت آنلاین، کلاس آنلاین.  
یک سازمان per instance؛ ثبت‌نام/پرداخت عمومی روی slug دوره و enrollment.

### School (`/admin/`, `/school-panel/`)
سال تحصیلی، پایه، رشته، کلاس، دانش‌آموز، ولی، ثبت‌نام سالانه.

### Control (`/control/`)
درخواست دمو، مشتریان، لایسنس‌ها، چک‌لیست نصب دستی.

---

## مستندات

- [Architecture Contract](./docs/architecture-contract.md)
- [Customer First Install](./docs/customer-first-install.md)
- [Hosting & Demo Map](./docs/hosting-and-demo.md)
- [Architecture Roadmap](./docs/architecture-roadmap.md)
- [Installation Branding](./docs/installation.md)
- [School Core](./docs/school-core-architecture.md)
- [Instance Upgrade](./docs/instance-upgrade.md)
- [Website Module](./docs/website-module.md)
- [AGENTS.md](./AGENTS.md) — راهنمای عامل/توسعه‌دهنده

وضعیت QA (architecture checkpoint): Full system regression **172 PASS / 0 FAIL / 2 SKIP**.  
محدودیت‌ها و deferred: بخش *Known limitations* در [`architecture-contract.md`](./docs/architecture-contract.md).

---

## استقرار

Docker:

```bash
docker compose build && docker compose up -d
```

جزئیات ارتقای هر Instance: [`docs/instance-upgrade.md`](docs/instance-upgrade.md)

---

**دانا (Dana)** — یک محصول، دو پروفایل مشتری، نصب‌های مستقل
