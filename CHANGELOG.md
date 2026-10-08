# Changelog — دانا (Dana)

وضعیت معماری فعلی و مرز پروفایل‌ها: [`docs/architecture-contract.md`](docs/architecture-contract.md).  
این فایل تاریخچهٔ محصولی/UI است؛ برای قوانین tenancy و kernel به قرارداد مراجعه کنید.

## 2026-10 — Fresh Academy install notes

- Empty-database Academy path verified: `install_config.py` → `.env` → `migrate` → `createsuperuser` → dashboard, after CSS build and `collectstatic`
- Academy has no `/admin/` and no organization settings screen; customer name is `init_academy_org.py --title`. Logo, phone, email, and address stay unset in the UI
- First-install doc now requires `tailwind build` before `collectstatic` on a clean tree

## 2026-10 — Installation identity file (`install_config.py`)

- `PRODUCT_MODE` و `WEBSITE_ENABLED` از `install_config.py` (نه `.env`)؛ loader: `config/install_loader.py`
- `.env` فقط secrets/infra؛ بدون dual-read از env برای محصول
- `DANA_INSTALL_FILE` برای تست/نصب جدا؛ بدون fallback خاموش به academy

## 2026-10 — Customer first-install foundation

- `PRODUCT_MODE` الزامی (بدون fallback خاموش به academy) — `config/settings.py`, `config/product_mode.py`
- `.env.example` و `docker-compose.yml` عمومی برای مشتری (بدون hostهای panel.aihousesb)
- `scripts/init_academy_org.py --title "..."`؛ حذف رفتار hardcode سان‌تک از init
- راهنما: [`docs/customer-first-install.md`](docs/customer-first-install.md) (`migrate` + `createsuperuser` + branding + SchoolProfile)

## 2026-10 — Hosting & demo architecture contract (docs only)

- سند [`docs/hosting-and-demo.md`](docs/hosting-and-demo.md): سایت مرکزی `edu-aihousesb.ir`، دموهای جدا Academy/School، نصب مشتری، Control داخلی؛ بدون ادغام پروفایل‌ها
- قفل مفهومی مسیرهای `/demo/academy/` و `/demo/school/` (proxy بعداً؛ هنوز پیاده‌سازی نشده)

## 2026-10 — Architecture checkpoint (docs + website CTA hooks)

- Website public CTAs از profile registry (`website_public_context`)؛ حذف قالب مرده `website/home.html`
- رگرسیون کامل سیستم / ایزولاسیون cross-profile: **172 PASS / 0 FAIL / 2 SKIP**
- همگام‌سازی اسناد منبع حقیقت با deferredهای شناخته‌شده (mount تکراری، exams path، GET logout، W003، …)

## 2026-10 — Profile isolation & Academy singleton

- سوئیچ پروفایل `config/profile.py` (academy / school / control)
- سازمان آموزشگاه singleton (`schools.School`)؛ حذف subdomain tenancy و `SchoolMiddleware`
- حذف اپ‌های مرده `apps.core` / `apps.accounting` و مسیر register چندمستاجری `apps.schools`
- تست‌ها: profile isolation، kernel purity، singleton، gateway
- اصلاحات QA: nested public pay (`slug`)، Forms `is_public`، SMS search (`Q`)، Control 403 fonts، teacher materials jalali filter

## تاریخی (Cademy / UI rebuild)

خلاصه کارهای تکمیل‌شده پیش از تفکیک پروفایل‌ها (لاگین OTP، دوره، ثبت‌نام، تخفیف، حسابداری، اقساط، گزارش، کارت شناسایی، آزمون، پیامک، پنل استاد/هنرجو، PWA). جزئیات قدیمی در git history باقی است.
