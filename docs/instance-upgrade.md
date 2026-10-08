# Instance upgrade runbook

Each customer runs an isolated Dana instance (own DB, media, `.env`, domain).
Upgrades are per-instance from the same codebase tag/commit.

**First install** (new customer): see [`customer-first-install.md`](customer-first-install.md)
(`migrate`, `createsuperuser`, branding, Academy org / SchoolProfile).

## Preconditions
- Know the instance `PRODUCT_MODE` from `install_config.py` (`academy` | `school` | `control`) — do not change it on an existing DB
- Backup database and `media/`
- Confirm `.env` has correct `DATABASE_URL`, secrets, and hosts
- Maintenance window agreed with customer

## Docker path (preferred)
```bash
cd /path/to/instance
git fetch --tags
git checkout <release-tag-or-commit>
docker compose build
docker compose up -d --remove-orphans
# entrypoint runs migrate + collectstatic
docker compose logs -f --tail=100
```

## Non-Docker / cPanel path
```bash
cd /path/to/instance
# backup DB + media first
git pull   # or upload release files
source venv/bin/activate   # or Windows equivalent
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py tailwind build   # if CSS sources changed
touch passenger_wsgi.py           # restart app
```

## Post-upgrade checks
1. Home / login loads for the profile
2. Admin can sign in
3. Academy only: create a test payment in staging or verify gateway env still set
4. SMS: send a test message if IPPanel credentials present
5. Static/media URLs resolve (Whitenoise / web server aliases)
6. Record version + date in Control → install notes for that customer

## Rollback
1. Redeploy previous git tag/commit
2. Restore DB backup taken before migrate
3. Restore media if files changed
4. Restart process / containers

## Do not
- Point multiple customer domains at one shared customer DB
- Run academy and school profiles against the same database
- Skip backup before migrate
