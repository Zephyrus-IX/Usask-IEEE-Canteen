# Initial deployment

This guide is for the first time you deploy the Usask IEEE Canteen app on a server or another PC using Docker Compose.

## 1. Clone the repository

```bash
git clone https://github.com/<owner>/Usask-IEEE-Canteen.git
cd Usask-IEEE-Canteen
```

If the repository is private, the deployment machine needs GitHub access through a user account, a fine-grained read-only token, or a read-only deploy key.

## 2. Create the environment file

```bash
cp .env.example .env
```

Edit `.env` before starting the stack:

```env
DJANGO_SECRET_KEY=<generate-a-long-random-secret>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=<server-ip-or-domain>,localhost,127.0.0.1

POSTGRES_DB=canteen
POSTGRES_USER=canteen
POSTGRES_PASSWORD=<strong-database-password>
DATABASE_URL=postgres://canteen:<strong-database-password>@db:5432/canteen
```

Notes:

- Do not reuse the example `DJANGO_SECRET_KEY` or database password for a real deployment.
- `DJANGO_ALLOWED_HOSTS` must include the hostname, LAN IP, or domain users will visit.
- Keep `.env` private. Do not commit it to GitHub.

## 3. Build and start Docker Compose

```bash
docker compose up -d --build
```

Check logs if the web container does not stay up:

```bash
docker compose logs web
```

On startup, the web container prints a reminder with the first-deploy commands below.

## 4. Run database migrations

```bash
docker compose exec web python manage.py migrate
```

This creates the Django tables, including the admin user table and canteen app tables.

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

- Student tabs
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
3. Add active student tabs.
4. Enter initial stock through restocks or inventory adjustments.
5. Test one small sale with an exec/admin account.

## Useful maintenance commands

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
docker compose up -d --build
docker compose exec web python manage.py migrate
```
