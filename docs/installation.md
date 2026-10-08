# ماژول تنظیمات و برندینگ (`apps.installation`)

هر Instance فیزیکی دانا یک رکورد singleton به نام `InstallationConfig` دارد
(برندینگ runtime؛ **نه** انتخاب محصول). انتخاب پروفایل (`academy` / `school` / `control`)
از `install_config.py` است.

برای راه‌اندازی اولین نصب مشتری (install_config، migrate، createsuperuser، سازمان Academy، SchoolProfile)
به [`customer-first-install.md`](customer-first-install.md) مراجعه کنید.

## ویژگی‌ها
1. **Singleton:** همیشه `pk=1`؛ متد `InstallationConfig.get_solo()`.
2. **مدیریت از Django Admin:** نام مجموعه، لوگو، فاوآیکون، رنگ اصلی/فرعی، تلفن، نشانی، ایمیل پشتیبانی، متن فوتر.
3. **Context processor:** کلید `installation` در تمام قالب‌ها در دسترس است.
4. **CSS variables:** قالب پایه رنگ‌ها را از `installation.primary_color` و `installation.secondary_color` تزریق می‌کند.

## First install (required before handover)
After `migrate` and `createsuperuser`, open Django admin and set this customer’s:

- `organization_name`
- `logo` / `favicon` (optional)
- `primary_color` / `secondary_color`
- `contact_phone` / `contact_address` / `support_email`
- `footer_text`

Default name on first `get_solo()` is a placeholder (`AI House EDU`) until you replace it with the **real customer name**. Do not leave the placeholder on a production handoff.

Do not invent a second branding system for this step.

## تست‌ها
- `apps/installation/tests.py` — singleton
- `apps/installation/tests_context.py` — context processor
