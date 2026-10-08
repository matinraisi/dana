# Optional Website module

## Policy
- Panel + PWA are always on for customer instances.
- Public website/landing is **optional** via `WEBSITE_ENABLED` in `.env`.
- AI and auto-provisioning remain deferred (see `architecture-contract.md`).
- **Central product marketing** for Dana (Academy + School story, demo entry
  points) is hosted on the Central Product Website environment described in
  [`hosting-and-demo.md`](hosting-and-demo.md) (`edu-aihousesb.ir`). That is
  distinct from optional website pages on a **customer** Academy/School install.
- Public paths `/demo/academy/` and `/demo/school/` on the central site are a
  **routing concept** to separate demo instances—not in-app merges of profiles.
  Proxy wiring and demo mode are not implemented in this module yet.

## Behavior
| `WEBSITE_ENABLED` | Root `/` |
|---|---|
| `True` (default) | `website` app: home / training / about / contact |
| `False` | Redirect to profile home (`Profile.root_redirect`) |

## Implementation (current)
- Views: `website/views.py` — `HomeView` uses template
  `theme/templates/website/cademy.html`.
- Authenticated users hitting `/` are redirected via
  `get_profile().resolve_authenticated_home(user)` (no hard-coded Academy
  dashboard URL in the Website app).
- Public CTAs (nav / hero / footer / training) are supplied by
  `Profile.website_public_context()` through
  `config.context_processors.product_context` (`website_cta_url`, labels,
  `website_extra_links`, closing copy).
- Website Python package must not import Academy / School / Control domain apps
  (enforced by `config.tests_profile_isolation`).

## Scope (v1)
- Landing page (`cademy.html`)
- Training / help page
- Simple About + Contact pages using `InstallationConfig` contact fields
- Profile-specific CTAs (Academy login + teacher/student links; School admin
  login; Control demo request)

Custom marketing sites for customers can still be delivered out-of-band until
richer templates exist.

## Deferred on purpose
- CMS / page builder
- Multi-template marketplace
- AI content generation
- Automated instance provisioning
- Fully profile-specific marketing copy on `/training/` (CTAs are already
  profile-safe; body copy may still read as Academy-oriented)
