# معماری و نقشه راه دانا

قرارداد قطعی: [`architecture-contract.md`](architecture-contract.md)

## معماری فعلی
- یک codebase با سه پروفایل نصب: `academy` / `school` / `control` (`PRODUCT_MODE` → `config/profile.py`)
- Tenancy تجاری: یک مشتری = یک Instance = یک DB
- داخل Academy Instance: **یک سازمان** (`schools.School` singleton) — بدون subdomain / `SchoolMiddleware`
- برندینگ Instance: `InstallationConfig` + context processor؛ Academy از org برندینگ هم می‌خواند
- Academy: محصول بالغ (دوره، مالی، آزمون، CRM، فرم‌ساز، پنل‌ها، پرداخت، ثبت‌نام عمومی)
- School: هسته داده + پنل vertical اول (`/school-panel/`) — بدون حضور/آزمون/مالی مدرسه
- Control: درخواست‌ها + مشتری + لایسنس + چک‌لیست نصب دستی
- Website اختیاری: CTAها از profile hooks (نه hard-code مسیر Academy)
- **Hosting map (قفل‌شده):** سایت مرکزی `edu-aihousesb.ir` + دموهای جدا Academy/School + نصب مشتری — [`hosting-and-demo.md`](hosting-and-demo.md)

## Shared kernel
`users`, `installation`, `notifications`, theme/PWA، الگوهای پرداخت، deploy / `verify_profile_schemas`.

اپ‌های مرده `apps.core` و `apps.accounting` حذف شدند.

## وضعیت QA (checkpoint)
Full system regression (STEP 21): **172 PASS / 0 FAIL / 2 SKIP**.  
جزئیات deferred و هشدارها در [`architecture-contract.md`](architecture-contract.md) بخش Known limitations.

## نقشه راه
1. **انجام‌شده:** قرارداد معماری، پروفایل‌ها و تست ایزولاسیون، singleton Academy Org، حذف tenancy middleware/filter، سخت‌سازی Academy + QA، PWA، Control registry، School vertical اول، Website اختیاری + CTAهای profile-aware، ایزولاسیون cross-profile، رگرسیون کامل سیستم، **قفل hosting/demo map**
2. **بعدی:** محتوای وب‌سایت دو‌محصولی برای `edu-aihousesb.ir`، نمونه دمو read-only (سروری) + داده نمونه، مسیر proxy برای `/demo/*` (ops)، سپس عمق School / بدهی URL Academy
3. **عمداً معوق:** provisioning نیمه‌خودکار، AI instance-local، bulk deploy — تا وقتی حجم فروش اجبار کند

## آنچه عمداً نمی‌سازیم الان
- Rewrite کامل
- Multi-tenant Academy در یک DB مشترک به‌عنوان مدل تجاری
- Plugin marketplace
- AI Core بزرگ
- Auto-provisioner کامل
