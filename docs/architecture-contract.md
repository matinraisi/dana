# Dana Architecture Contract (frozen)

This document is the source of truth for product boundaries. Older docs that
conflict with it are outdated.

## Product

Dana is **one Education Platform** shipped from **one codebase**, with three
install profiles selected by `PRODUCT_MODE` in `install_config.py`
(loaded into `settings.PRODUCT_MODE` → `config/profile.py`). Product identity
is **not** read from `.env` (secrets/infra only). Runtime branding remains in
DB `InstallationConfig`.

| Mode | Purpose |
|---|---|
| `academy` | Customer instance for training centers (آموزشگاه) |
| `school` | Customer instance for K-12 schools (مدرسه) |
| `control` | Dana operator plane (sales, customers, licenses) — never a customer tenant |

Academy and School are **product profiles**, not separate repositories. Each
profile owns its domain model, roles, and workflows. Shared code is a narrow
kernel only.

## Commercial tenancy

**One customer → one instance → one database → own domain/media/settings.**

This is SaaS at the product and provisioning level, not multi-tenant rows in a
shared customer database. There is **no subdomain tenancy** and **no
`SchoolMiddleware` / `SchoolFilterMixin`** in the active stack.

### Hosting map & demos (frozen)

Public product site, demo instances, and customer installs are specified in
[`hosting-and-demo.md`](hosting-and-demo.md). Summary:

| Environment | Role |
|---|---|
| Central Product Website (`edu-aihousesb.ir`) | Marketing for **both** Academy and School; request/demo contact; public paths `/demo/academy/` and `/demo/school/` (edge routing to demo backends — ops later) |
| Academy Demo Instance | Separate install with `PRODUCT_MODE = "academy"` in `install_config.py` + **own DB**; read-only (server-side when implemented) |
| School Demo Instance | Separate install with `PRODUCT_MODE = "school"` in `install_config.py` + **own DB**; read-only (server-side when implemented) |
| Customer Academy / School | Independent paid installs; never share DB with demos or each other |
| Internal Control | Customers / licenses / installs; not a public product line |

**Do not** merge Academy and School into one `PRODUCT_MODE` or one shared demo DB.
Demo enforcement, reverse proxy, website rewrite, and demo seeds are **later
implementation steps**—this contract only locks the map.

### Academy org rule (singleton)

Inside an Academy instance there is **exactly one organization**.

- Canonical model: `apps.schools.School` (legacy app name; means Academy Org).
- Enforced in `School.clean` / `School.save` and migration
  `schools.0003_singleton_academy_organization`.
- Helpers: `apps.academy.org.get_instance_organization` /
  `set_organization` / `OrganizationMembership`.
- Branding fallback: `apps.installation.InstallationConfig` (kernel singleton)
  plus Academy context processor `apps.schools.context_processors.school_context`.
- Optional FK “school stamps” on Academy domain rows (e.g. `Course.school`,
  `SMSLog.school`) are **not** multi-tenant switches; they point at the
  singleton org or may be null.

### Naming (avoid collisions)

| Term | Meaning |
|---|---|
| Academy Org | Customer organization inside an academy instance (`apps.schools.School`) |
| School Product | K-12 profile (`apps.school_management`) |
| SchoolProfile | Singleton identity of one school install |

Never map School Product students/classes onto `apps.academy` models.
Do not confuse `apps.schools` (Academy Org, legacy name) with School Product.

## Shared kernel (narrow)

Allowed shared pieces:

- `apps.users` — auth primitives; roles gated by profile
- `apps.installation` — instance branding/settings singleton
- `apps.notifications` — SMS transport (IPPanel only; no product logs)
- payment gateway client patterns (academy payment flow today)
- `theme` / PWA shell
- deploy and upgrade tooling (`config/profile.py`, `scripts/verify_profile_schemas.py`)

Do **not** invent shared Student / Course / Enrollment / Attendance abstractions
across Academy and School.

Dead apps `apps.core` and `apps.accounting` were removed; they are not part of
any profile.

## Profile boundaries

### Academy (`PRODUCT_MODE=academy`)

Owns: courses, enrollments, finance/installments, exams, attendance, SMS logs,
CRM, forms builder, teacher/student panels, public registration/payment.

URL tree: `apps.academy.urls_profile` → `/dashboard/`, `/teacher/`, `/my/`,
`/crm/`, `/forms/`, `/auth/`, `/register/<slug>/`, `/pay/<id>/`,
`/payment/gateway/…`, `/verify/<card>/`.

Roles: admin staff (`OWNER` / `PARTNER` / `MANAGER_*` via `is_admin_staff`) →
dashboard; `TEACHER` → `/teacher/`; `STUDENT` → `/my/`. OTP + password under
`/auth/`.

### School (`PRODUCT_MODE=school`)

Owns: academic years, grades, fields, classrooms, students, guardians,
school enrollments. Domain lives only in `apps.school_management`.

URL tree: `apps.school_management.urls_profile` → `/admin/`, `/school-panel/`.

Implemented vertical: profile, years, structure, students, guardians,
enrollments. Attendance / exams / finance modules for School are **not**
implemented (deferred).

### Control (`PRODUCT_MODE=control`)

Owns: demo/provisioning requests, customers, licenses, install inventory.
No customer operational data. URL tree: `apps.control_center.urls_profile`.

Implemented: public request form, request list/update (POST), customer /
license / install CRUD. Operator “dashboard/settings” product UI is deferred;
superuser Django admin remains available.

## Website (optional)

- Toggle: `WEBSITE_ENABLED` (see [`website-module.md`](website-module.md)).
- Landing template: `theme/templates/website/cademy.html` (not a dead
  `home.html`).
- Public CTAs come from **profile registry hooks**
  (`Profile.website_public_context` → `config.context_processors.product_context`).
  Templates must not hard-code Academy URLs or branch CTAs on raw
  `PRODUCT_MODE`.

## Auth and role boundaries

- Kernel: `apps.users.User` + `OTPToken`; panel mixins in
  `apps.users.mixins.RoleRequiredMixin`.
- Academy admin gates: `apps.academy.mixins.AdminRequiredMixin`
  (`school_object_or_404` is a plain `get_object_or_404` helper — not tenancy).
- Teacher/student must not access Academy admin, CRM, Forms admin, or SMS tools
  (HTTP 403).
- Forms builder ownership is `created_by`; public forms require
  `is_active=True` **and** `is_public=True`.
- Academy logout view is Django `LogoutView` (POST). Templates should POST;
  any remaining GET logout link is debt (see deferred).

## Migrations and database strategy

- One DB per instance; `PRODUCT_MODE` selects installed apps and thus which
  migrations apply.
- Fresh DBs: `python manage.py migrate` under the target mode.
- Schema isolation check: `python scripts/verify_profile_schemas.py`.
- Academy org singleton data migration: `schools.0003_*`.
- Users kernel migrations were compacted to `0001_initial` + `0002_otptoken`
  (do not resurrect deleted intermediate user migrations).
- Do not recreate production DBs for routine upgrades; see
  [`instance-upgrade.md`](instance-upgrade.md).

## Modules

| Module | Policy |
|---|---|
| Panel + PWA | Always on for customer instances |
| Website | Optional per instance (`WEBSITE_ENABLED`) |
| AI | Deferred; when added, instance-local data only |
| Auto-provisioning | Deferred; Control starts as manual registry/checklist |

## Explicitly rejected

- Two separate product repos for Academy and School
- Full rewrite of Dana
- Multi-tenant Academy SaaS in one shared DB as the long-term commercial model
- Subdomain / middleware tenancy inside an Academy instance
- Merging School Product into `apps.academy`
- Early AI platform / plugin marketplace / full auto-provisioner

## Completed (current codebase)

- Profile switchboard (`config/profile.py`) + isolation / kernel purity tests
- Academy singleton Organization + schema isolation script
- Removal of `SchoolMiddleware`, multi-org school filter mixin, dead
  `apps/schools` register URLs/views/templates, dead `apps/admin_base.py`
- Control customers / licenses / installs
- School first vertical (`/school-panel/`)
- Optional website module with **profile-aware public CTAs**
- Cross-profile isolation QA + full system regression (STEP 21):
  **172 PASS / 0 FAIL / 2 SKIP** (temp DBs; see deferred for skips/warnings)

## Known limitations / deferred

### Academy URL / UX debt (non-blocking)

- **Duplicate public mounts:** root mounts in `urls_profile`
  (`/register/<slug>/`, `/pay/<id>/`, `/verify/<card>/`) plus overlapping
  paths/names under `apps.academy.urls` (`/dashboard/register/…`,
  `/dashboard/pay/…`, `/dashboard/verify/…`) and nested routes in
  `urls_public`. Canonical public links use root `/register/`, `/pay/`,
  `/verify/`. Prefer consolidating later (ISS-040b).
- **Misplaced student exams URL:** `academy:student_exams` is mounted at
  `/dashboard/my/exams/` (admin URL tree) rather than under `/my/`.
  Student panel still has its own surfaces; consolidate later.
- **POST-only logout:** `AcademyLogoutView` expects POST. Dashboard/student
  templates use forms; `theme/templates/teacher/base.html` still has one
  GET `<a href="{% url 'academy:logout' %}">` that will 405 if used.

### Naming / data stamps

- `apps.schools` remains the **Academy Org** app (legacy name). School Product
  lives in `apps.school_management` only.
- Academy FK stamps to `schools.School` are singleton org references, not
  multi-tenant routing.

### School Product (unimplemented)

- No School attendance, exams, SMS product logs, finance, or teacher/student
  portals beyond staff `/school-panel/` + `/admin/`.

### Control (unimplemented)

- No dedicated operator dashboard/settings product UI beyond request /
  customer / license / install lists and Django admin.
- `ProvisioningRequestUpdateView` is POST-only (status/note update from list
  UI); GET → 405 by design.

### Website

- Richer multi-template / CMS website is deferred.
- Training page still contains Academy-oriented marketing copy; CTAs are
  profile-safe.

### Fresh Academy install (verified 2026-10-08)

Empty Academy database: `migrate`, `createsuperuser`, and `/dashboard/` succeed when static files are already collected. Identity source is `install_config.py`, not `.env`.

Still manual / not in the Academy UI:

- Tailwind build plus `collectstatic` before first login on a clean tree (manifest storage, `DEBUG=False`).
- Organization **title** via `scripts/init_academy_org.py --title`. Logo, phone, email, and address have no Academy screen. `/admin/` is not on the Academy URL tree, so `InstallationConfig` is not editable there. Next step is one dashboard organization form, not a new branding model and not mounting full Django Admin.

### Tooling / environment warnings

- **templates.W003:** both `theme.templatetags.custom_filters` and
  `apps.academy.templatetags.custom_filters` register the library name
  `custom_filters` when Academy is installed (Academy wins for jalali helpers;
  theme copy keeps School/Control admin formatting). Non-blocking warning.
- **Host disk:** local C: may be nearly full; run temp DBs / `collectstatic`
  targets on D: (or other spacious volume). `ENOSPC` on C: is an environment
  issue, not an application defect.

### Other product debt

- `SMSLog.school` often null on bulk send; SMS template CRUD absent; forms
  publish flags set on create only; public pay-by-enrollment_id is an
  intentional unauthenticated capability link; IPPanel failures must not 500.
- Broader backlog: [`ISSUES.md`](../ISSUES.md).

## Remaining work (next, not this checkpoint)

1. Customer-branded landing (website still Dana-oriented when `WEBSITE_ENABLED=True`)
2. Dual-product central website content for `edu-aihousesb.ir` (see hosting map)
3. Demo instances + server-side read-only mode + sample data (see
   [`hosting-and-demo.md`](hosting-and-demo.md)) — after hosting map is locked
4. Edge/reverse-proxy wiring for `/demo/academy/` and `/demo/school/` (ops; not
   app rewrite)
5. School Product workflow depth (attendance/exams/… as product decisions)
5. Optional consolidation of duplicate Academy public URL mounts + student exams path
6. Fix residual GET logout link in teacher template
7. Resolve or silence `custom_filters` W003 deliberately
8. Semi-automated provisioning / AI — only when sales volume requires it
9. Continue ISSUES.md P1 items (finance hardening, student forms, SMS dedup)

## Evolution path

1. Contract + docs (this file) — done
2. Harden Academy (security, branding, PWA, upgrades, singleton org) — largely done
3. Grow Control (customers, licenses, install notes) — done for manual registry
4. School first vertical — done; deepen next
5. Optional website module — done (`WEBSITE_ENABLED` + profile CTA hooks)
6. Later: semi-automated provisioning, AI

## Architecture test commands

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test config.tests_profile_isolation apps.users.tests_kernel_purity apps.schools.tests_singleton apps.academy.tests_gateway
python scripts/verify_profile_schemas.py
```
