# Initial deployment

This guide is for the first time you deploy the Usask IEEE Canteen app on a server or another PC using Docker Compose.

## 1. Clone the repository

```bash
git clone https://github.com/<owner>/Usask-IEEE-Canteen.git
cd Usask-IEEE-Canteen
```

If the repository is private, the deployment machine needs GitHub access through a user account, a fine-grained read-only token, or a read-only deploy key.

## 2. Configure the environment file

Dockhand reads the committed `.env` template directly. Edit `.env` in Dockhand or on the deployment host before starting the stack. The file contains placeholders only; do not commit real generated secrets back to GitHub.

Required production values:

```env
DJANGO_SECRET_KEY=<generate-a-long-random-secret-of-at-least-50-characters>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=<server-ip-or-domain>,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_TRUST_CLOUDFLARE_HEADERS=0
DJANGO_SECURE_COOKIES=0
DJANGO_SECURE_SSL_REDIRECT=0
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=0
DJANGO_SECURE_HSTS_PRELOAD=0

POSTGRES_DB=canteen
POSTGRES_USER=canteen
POSTGRES_PASSWORD=<strong-database-password>
DATABASE_URL=postgres://canteen:<strong-database-password>@db:5432/canteen
```

Notes:

- Generate the Django secret with `python -c "import secrets; print(secrets.token_urlsafe(64))"` and copy the result into `.env`.
- The container refuses to start with a missing, placeholder, or short `DJANGO_SECRET_KEY` while `DJANGO_DEBUG=0`.
- Do not reuse the example database password for a real deployment.
- Generate a separate database password and URL-encode it when placing it inside `DATABASE_URL`; the Compose stack refuses to start if either database variable is missing.
- `DJANGO_ALLOWED_HOSTS` must include the hostname, LAN IP, or domain users will visit.
- Keep real `.env` values private. The committed `.env` file is a Dockhand template only; do not commit the generated secret values.
- While testing authenticated pages over plain LAN HTTP, leave secure cookies and HTTPS redirects disabled.
- At the Cloudflare Tunnel cutover, set the exact public hostname in `DJANGO_ALLOWED_HOSTS`, set `DJANGO_CSRF_TRUSTED_ORIGINS=https://<exact-hostname>`, and set `DJANGO_TRUST_CLOUDFLARE_HEADERS=1`, `DJANGO_SECURE_COOKIES=1`, and `DJANGO_SECURE_SSL_REDIRECT=1`.
- Leave HSTS disabled until the exact HTTPS hostname has been tested. Enable it gradually afterward; do not enable subdomain coverage or preload without reviewing every affected hostname.

## 3. Build and start Docker Compose

For the current plain-HTTP LAN test deployment, explicitly include the LAN override:

```bash
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
```

The base `compose.yaml` exposes Gunicorn only to other containers. This prevents bypassing Cloudflare once the tunnel service is added. `compose.lan.yaml` is only for temporary trusted-LAN testing and publishes host port `8000`.

Check logs if the web container does not stay up:

```bash
docker compose logs web
```

On startup, the web container applies database migrations, collects static files, and prints a reminder with the first-deploy commands below.
The application is served by Gunicorn; WhiteNoise serves the collected static files.

## 4. Run database migrations

```bash
docker compose exec web python manage.py migrate
```

Startup already applies migrations. This command is safe to run again and verifies that the Django tables are current.

## 5. Create the first Django admin account

```bash
docker compose exec web python manage.py createsuperuser
```

You will be prompted for:

```text
Username:
Email address:
Password:
Password again:
```

Use a named IEEE exec/admin account rather than a shared password when possible. Add more users later through Django admin.

## 6. Log in to Django admin

Open:

```text
http://<server-ip-or-domain>:8000/admin/
```

Use the superuser account created in the previous step.

The canteen models currently registered in Django admin include:

- Student accounts
- Inventory items
- Tax rates
- Sales
- Balance transactions
- Restock events
- Inventory adjustments

## 7. Initial app setup checklist

After the first admin login:

1. Add any tax rates needed for restock tracking.
2. Add inventory items with member and non-member prices.
3. Add active student accounts.
4. Enter initial stock through restocks or inventory adjustments.
5. Test one small sale with an exec/admin account.

Creating a student account uses the NSID as its username and shows a generated temporary password once. Give that password directly to the student. The student must create a private password at first sign-in. Student Numbers are not collected or stored.

An executive can generate a replacement temporary password from the student's account page. This immediately invalidates the old password and requires password creation again. Five failed attempts for the same NSID and source IP produce a 15-minute automatic lockout.

Migration `0004` removes Student Number and invalidates passwords for every pre-existing non-staff customer account. It intentionally stops before removing the identifier if any old account has no linked NSID user. Because current installations contain test data only, delete/recreate those accounts or reset the test database before upgrading; linked accounts can instead receive a new temporary password after migration.

## Useful maintenance commands

## Update procedure without resetting the database

For normal updates, do **not** remove volumes. The PostgreSQL data lives in the Docker volume `postgres_data`, and deleting that volume resets accounts, inventory, sales, balances, and the admin user.

Use this update flow from the same repository directory you originally deployed from:

```bash
git pull origin dev
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
docker compose -f compose.yaml -f compose.lan.yaml logs -f web
```

The web container runs migrations and `collectstatic` automatically before Gunicorn starts. You can verify migrations afterward with:

```bash
docker compose -f compose.yaml -f compose.lan.yaml exec web python manage.py showmigrations canteen
```

Safe commands for preserving data:

```bash
docker compose -f compose.yaml -f compose.lan.yaml stop
docker compose -f compose.yaml -f compose.lan.yaml down
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
```

Destructive reset command:

```bash
docker compose -f compose.yaml -f compose.lan.yaml down -v
```

Only use `down -v` when you intentionally want to delete the local test database and start over. A plain `docker compose down` should keep the named volume, but deploying from a different folder/project name can create a different Compose volume and make the app look empty. Keep using the same checkout directory, or set a stable project name with `COMPOSE_PROJECT_NAME=usask-ieee-canteen` before the first deploy.

Create another admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Change an admin password:

```bash
docker compose exec web python manage.py changepassword <username>
```

Apply future database migrations after pulling updates:

```bash
git pull
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
docker compose exec web python manage.py migrate
```
