# Usask IEEE Canteen

A self-hosted Docker app to manage and track inventory, in-person sales, student accounts, prepaid balances, restocks, and expenses for the Usask IEEE student branch canteen.

## Project goals

- Public customer self-service plus exec-facilitated in-person sales
- Every sale must be attached to an active student account
- Student accounts are created by an admin/IEEE exec
- Student Numbers are not collected; NSID is the login username
- One-time temporary passwords require students to create a private password at first sign-in
- Login attempts are locked for 15 minutes after five failures for the same NSID and source IP
- Sales use prepaid student account balances only
- IEEE member and non-member pricing
- Inventory automatically decreases on completed sales
- Restocks are manually entered and increase inventory
- Restock GST/PST/LST tracking with configurable tax rates
- CSV exports for sales, balances, restocks, inventory, and student accounts
- Web UI first, CLI/TUI fallback later

## Planned stack

- Django backend and web UI
- Gunicorn application server with WhiteNoise static-file serving
- PostgreSQL database
- Docker Compose deployment
- Future Python CLI/TUI sharing the same backend logic

## Repository layout

```text
backend/             Django project and canteen app
compose.yaml         Local/self-hosted Docker Compose stack
compose.lan.yaml     Explicit host-port override for temporary LAN testing
docs/                Design notes, deployment guide, and MVP scope
.env.example         Example environment variables
```

## Deployment

See [docs/initial-deployment.md](docs/initial-deployment.md) for first-deploy setup, database migrations, and Django admin account creation.

Future work, including encrypted PostgreSQL exports to removable USB storage, is tracked in [docs/roadmap.md](docs/roadmap.md).

Quick start:

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

The LAN override publishes port `8000` only for pre-tunnel testing. The base Compose file keeps Gunicorn internal so a future `cloudflared` service can reach `web:8000` without creating a direct public origin bypass.

## Development status

Prototype planning/skeleton stage.
