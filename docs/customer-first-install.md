# Customer first install (Academy / School)

One customer = one independent installation (own `install_config.py`, `.env`, database, media, domain).
Do **not** share a database across customers or across Academy and School profiles.

This is the **first-install** runbook. Upgrades: [`instance-upgrade.md`](instance-upgrade.md).
Hosting map (central site / demos): [`hosting-and-demo.md`](hosting-and-demo.md) — not required for a customer handoff.

## Configuration layers

| Layer | File / store | Contents |
|---|---|---|
| Bootstrap identity | `install_config.py` | `PRODUCT_MODE`, `WEBSITE_ENABLED` |
| Infrastructure / secrets | `.env` | `SECRET_KEY`, `DATABASE_URL`, hosts, SMS, payments, paths |
| Runtime branding | `InstallationConfig` (DB) | name, logo, colors, phone, email, address, footer |

Product is **not** selected from `.env`. Changing `PRODUCT_MODE` on an existing database is unsupported.

## 0. Before you start

- Agree product: **Academy** or **School** (never both on one DB).
- Customer domain (HTTPS).
- Customer display name (organization / school name).
- Optional: logo, phone, email, address for branding.
- Optional: SMS (IPPanel) and payment credentials — only if sold for this install.

## 1. Prepare the instance directory

1. Deploy this codebase to the customer server (git clone/checkout or release copy).
2. Copy `install_config.example.py` → `install_config.py` and set:
   - `PRODUCT_MODE = "academy"` or `"school"` (**required**; missing/invalid refuses to start)
   - `WEBSITE_ENABLED = False` recommended until a customer-branded landing exists
3. Copy `.env.example` → `.env` and fill **required** secrets/infra only:
   - `SECRET_KEY` — unique per customer
   - `DATABASE_URL` — empty dedicated DB for this customer
   - `ALLOWED_HOSTS` — customer domain (+ `localhost` if you use the sample Docker healthcheck)
   - `CSRF_TRUSTED_ORIGINS` — `https://customer-domain`
   - `STATIC_ROOT` / `MEDIA_ROOT` — paths for this host
4. Leave SMS/payment blank until those features are enabled for the customer.
5. Do **not** put `PRODUCT_MODE` or `WEBSITE_ENABLED` in `.env`.

Optional local alternate files: `DANA_INSTALL_FILE` (identity) and `DANA_ENV_FILE` (secrets).

## 2. Database and migrations

```bash
python manage.py migrate
```

This applies only the apps for the `PRODUCT_MODE` in `install_config.py`.

## 3. First admin (required)

Do **not** auto-create users. Create one operator account:

```bash
python manage.py createsuperuser
```

Store credentials only in your secure handover channel — never in the repo or fixtures.

## 4. Branding

`InstallationConfig` is the instance branding record (name, logo, colors, phone, address, email, footer). The first page view creates it with the placeholder name `AI House EDU` if it does not exist yet.

**School:** after login, save the real school on `/school-panel/profile/` (section 5B). Django admin at `/admin/` can also edit `InstallationConfig`.

**Academy:** the panel title comes from the Academy Organization (`schools.School`), not from Django Admin. `/admin/` is not mounted on an Academy install. Set the customer name with `init_academy_org.py` (section 5A). Logo, phone, email, and address exist on that organization and on `InstallationConfig`, but there is no Academy dashboard screen for them yet. Do not treat Django Admin as the Academy handover UI.

## 5A. Academy-only — organization singleton

Only when `PRODUCT_MODE = "academy"` in `install_config.py`, after migrate + createsuperuser:

```bash
python scripts/init_academy_org.py --title "نام واقعی آموزشگاه مشتری"
# optional:
# python scripts/init_academy_org.py --title "..." --slug customer-slug
```

- Creates the singleton `apps.schools.School` (Academy Org) owned by the superuser.
- Does **not** invent Suntech or other fake demo data.
- If the org already exists, the script reuses it (use `--force-title` only to rename).
- Deprecated alias: `scripts/init_school.py` (forwards to the same command; still requires `--title`).

Then log in at `/dashboard/login/` and verify the dashboard loads.

## 5B. School-only — SchoolProfile (required before handover)

Only when `PRODUCT_MODE = "school"` in `install_config.py`:

1. Log in at `/admin/login/` with the superuser (must be staff).
2. Open `/school-panel/profile/` and save **SchoolProfile** with the real school name
   (and phone/address as available).
   - Or create the singleton via school Django admin if preferred.
3. Installation is **not ready for handover** until `SchoolProfile` exists with the
   customer school name.
4. Optional before handover: create the first academic year under `/school-panel/years/`
   (operator or customer). Not required to “boot,” but recommended for a usable start.
5. Do **not** promise attendance, exams, finance, or teacher/student portals in this
   vertical — they are not part of the current School product.

## 6. Static / media

A fresh checkout does not include the built CSS or the WhiteNoise manifest (`theme/static/css/dist/` and `staticfiles/` are gitignored). With `DEBUG=False`, `/dashboard/login/` raises `Missing staticfiles manifest entry for 'css/dist/styles.css'` until both commands below have been run against this instance's `STATIC_ROOT`.

```bash
# once per machine, inside theme/static_src, if node_modules is missing
npm install
python manage.py tailwind build
python manage.py collectstatic --noinput
```

On Windows the default `NPM_BIN_PATH` is `C:\Program Files\nodejs\npm.cmd`. On another host set `NPM_BIN_PATH` in `.env` if `npm` is not on that path. Restart the process after `collectstatic` so it reloads `staticfiles.json`.

Ensure the web server (or WhiteNoise + volume mounts) can serve `STATIC_ROOT` and
`MEDIA_ROOT`. Docker: see root `docker-compose.yml` (generic; adjust ports/volumes
per customer). Supply `install_config.py` in the app directory; `.env` supplies secrets only.

## 7. First login checks

| Profile | Login | Expect |
|---|---|---|
| Academy | `/dashboard/login/` | Admin dashboard after auth |
| School | `/admin/login/` then `/school-panel/` | Panel home; profile saved |

## 8. Control registry (Dana internal, optional but recommended)

On the **Control** instance (not the customer server), create/update:

- Customer
- License (manual record only — no runtime lock)
- InstallRecord (domain, `PRODUCT_MODE`, checklist: DNS, SSL, env, migrate, admin, handover)

## 9. Handover package

Give the customer:

- Site URL(s)
- Admin username (password via secure channel)
- Confirmation of Academy vs School
- Whether website is on/off
- What is **not** included (especially School limitations)
- How updates will be applied ([`instance-upgrade.md`](instance-upgrade.md))

## Do not

- Share one DB between customers or between Academy and School
- Run `init_academy_org.py` on a School install
- Rely on a missing `install_config.py` / `PRODUCT_MODE` (startup must fail)
- Put product selection in `.env`
- Commit real `.env` secrets or a customer-specific `install_config.py` to the shared repo
- Auto-provision servers or enforce licenses in this phase
