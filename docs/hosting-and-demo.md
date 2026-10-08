# Hosting map & demo architecture (frozen)

This document locks the **commercial hosting model** and **demo placement** for Dana.
It does **not** change profile isolation. Implementation of reverse proxy, demo
read-only mode, website redesign, and demo data are **out of scope for this
document** (design only until a later product step).

Source of truth for product boundaries remains
[`architecture-contract.md`](architecture-contract.md).
This file is the source of truth for **which physical environments exist** and
**how demos relate to them**.

---

## Non-negotiable rules

1. **One Git repository / one codebase** for all environments.
2. **Academy and School stay separate profiles** (`PRODUCT_MODE = "academy"` vs
   `"school"` in each instance’s `install_config.py`). They are **never** merged into one install/DB.
3. **Do not** load Academy domain apps and School domain apps in the same
   running instance.
4. **One customer → one installation → one profile → one database → one (or
   more) domains → own branding/settings.**
5. **Demo Academy** and **Demo School** are **separate installations**, each
   with its **own database and environment**. They must **never** share an
   Academy/School database with each other or with any customer.
6. Demo safety is **server-side** (middleware / env gates / disabled services),
   not “hide buttons in HTML” alone.
7. **No automatic provisioning** and **no license lock enforcement** in this
   phase. Bulk/scripted updates may come later; **manual updates per instance**
   remain the supported path now
   ([`instance-upgrade.md`](instance-upgrade.md)).

---

## Environment catalog

| Environment | Intended host / URL role | `PRODUCT_MODE` | Responsibility |
|---|---|---|---|
| **Central Product Website** | `edu-aihousesb.ir` (public marketing site) | Prefer `control` (website + lead form; Control UI stays internal) | Present **both** Academy and School as products; product info; demo entry points; request/demo contact flow. **Not** a customer classroom system. |
| **Academy Demo Instance** | Backend for public path `/demo/academy/` (routing TBD) | `academy` | Real Academy UI with **sample data**, **read-only**. Showcase Academy capabilities. |
| **School Demo Instance** | Backend for public path `/demo/school/` (routing TBD) | `school` | Real School UI with **sample data**, **read-only**. Showcase School capabilities. |
| **Customer Academy Installation** | Customer domain (e.g. `customer-domain.com`) | `academy` | Full (or contracted) Academy ops for that customer; own DB, branding, SMS/payment credentials. |
| **Customer School Installation** | Customer domain (e.g. `school-domain.com`) | `school` | School product for that customer; own DB and branding. |
| **Internal Control** | Separate internal host (or same Control instance as central site, staff-only paths) | `control` | Manual registry: customers, licenses, install inventory, request inbox. **Not** a public product section in phase 1. |

Notes:

- The **central website** and **Internal Control** may share one Control-mode
  instance (public pages + `/control/request/` vs staff `/control/…`), or be
  split later. Public marketing must **not** advertise Control as a customer
  product.
- Customer installations should typically use branding via
  `apps.installation.InstallationConfig` and may disable or replace the Dana
  marketing website (`WEBSITE_ENABLED`) so customers see **their** brand, not
  the Dana sales catalog.

---

## Hosting map (logical)

```text
                    ┌─────────────────────────────────────┐
                    │  edu-aihousesb.ir                     │
                    │  Central Product Website              │
                    │  (prefer PRODUCT_MODE=control)        │
                    │  - Academy product story              │
                    │  - School product story               │
                    │  - Request / demo contact             │
                    │  - Public paths:                      │
                    │      /demo/academy/  ──┐              │
                    │      /demo/school/   ──┼── routing    │
                    └────────────────────────┼──────────────┘
                                             │
              (reverse proxy / edge routing — NOT implemented yet)
                                             │
              ┌──────────────────────────────┴──────────────┐
              ▼                                             ▼
┌─────────────────────────────┐           ┌─────────────────────────────┐
│ Academy Demo Instance       │           │ School Demo Instance        │
│ PRODUCT_MODE=academy        │           │ PRODUCT_MODE=school         │
│ own DB + install_config +.env│          │ own DB + install_config +.env│
│ DEMO read-only (future)     │           │ DEMO read-only (future)     │
│ same codebase               │           │ same codebase               │
└─────────────────────────────┘           └─────────────────────────────┘

Customer A (academy)     Customer B (school)     Internal Control ops
own domain + DB          own domain + DB         customers / licenses /
PRODUCT_MODE=academy     PRODUCT_MODE=school     installs (manual)
```

---

## Public demo URL routing (concept only)

| Public URL on central site | Routes to | Backend profile |
|---|---|---|
| `https://edu-aihousesb.ir/demo/academy/` | Academy Demo Instance (path or upstream origin) | `academy` |
| `https://edu-aihousesb.ir/demo/school/` | School Demo Instance | `school` |

### Intent

- Visitors see **stable public paths** under the product domain.
- Edge/reverse-proxy (nginx, Cloudflare, host panel, etc.) may forward those
  paths (or equivalent hostnames) to the matching demo installation.
- **Reverse proxy configuration is not implemented in this repository step.**
  Document the contract only; deploy wiring is a later ops task.

### What routing must preserve

- Demo Academy traffic never hits a School DB or School `PRODUCT_MODE` process.
- Demo School traffic never hits an Academy DB or Academy `PRODUCT_MODE` process.
- Customer installations are unrelated origins/DBs; demos must not write into
  customer data.

### Acceptable future variants (still isolated)

- Path-based proxy: `edu-aihousesb.ir/demo/academy/` → `demo-academy` upstream.
- Hostname-based: `demo-academy.edu-aihousesb.ir` with central site linking to
  `/demo/academy/` as a redirect—**as long as** public marketing still presents
  clear Academy vs School demo entry points and databases stay separate.

---

## Demo instance requirements (contract; not implemented yet)

When demo mode is implemented later, each demo installation must satisfy:

### Isolation

- Separate `DATABASE_URL` (and media root) from every customer and from the
  other demo.
- Separate `.env` / secrets; demo credentials must not be production customer
  secrets.

### Read-only (server-side)

Enforcement must be **server-side**, not only UI hiding:

- Block create / update / delete of business data (HTTP mutating methods and
  view/form paths that persist changes).
- Disable or hard-fail: **payment** initiation/settlement, **SMS** send,
  **settings/branding mutation**, **file uploads** that alter state,
  **destructive** actions (delete, bulk wipe), and other **external
  side-effects** (webhooks that mutate, gateway calls, etc.).
- GET browsing of real product surfaces (dashboard/panel lists/details) remains
  allowed for demo users.

### Same product surfaces

- Prefer the **same** Academy / School views and templates as customer installs
  (`apps.academy.*`, `apps.school_management.*`, panels), gated by demo env—not
  a fake static “demo landing” that only looks like the product.

### Sample data

- Demo DBs may be seeded with realistic sample data (future step). Seeds must
  never target customer DBs.

---

## Responsibility summary

| Who | Does |
|---|---|
| Central Product Website | Sell/explain Dana; dual product story; lead capture; link/route into demos |
| Academy Demo | Safe tour of Academy UI |
| School Demo | Safe tour of School UI |
| Customer Academy / School | Production (or paid) ops for that org only |
| Internal Control | Dana team: track requests, customers, licenses, installs; **manual** deploy/upgrade notes |

---

## Updates & bulk deployment

- Today: upgrade **each instance** from the same git tag/commit
  ([`instance-upgrade.md`](instance-upgrade.md)).
- Future: scripted/bulk updates across many instances are **compatible** with
  this map (same codebase, many envs) but are **not** built in this phase.
- Do **not** implement auto-provisioning of servers/DBs from Control here.

---

## Explicitly out of scope for this document freeze

- Reverse proxy / nginx / Cloudflare config in-repo
- `DEMO_READONLY` (or equivalent) implementation
- Website template rewrite for dual product marketing
- Demo fixture/seed commands
- Merging Academy + School into one `PRODUCT_MODE`
- License enforcement on customer instances

---

## Related docs

- [`architecture-contract.md`](architecture-contract.md) — profile/kernel rules
- [`website-module.md`](website-module.md) — optional website module behavior
- [`instance-upgrade.md`](instance-upgrade.md) — per-instance upgrade runbook
- [`school-core-architecture.md`](school-core-architecture.md) — School product scope
