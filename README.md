# Usask IEEE Canteen

A self-hosted Docker app to manage and track inventory, in-person sales, student accounts, prepaid balances, restocks, and expenses for the Usask IEEE student branch canteen.

## Project goals

- Public customer self-service plus exec-facilitated in-person sales
- Every sale must be attached to an active student account
- Student accounts are created by an admin/IEEE exec
- Sales use prepaid student account balances only
- IEEE member and non-member pricing
- Inventory automatically decreases on completed sales
- Restocks are manually entered and increase inventory
- Restock GST/PST/LST tracking with configurable tax rates
- CSV exports for sales, balances, restocks, inventory, and student accounts
- Web UI first, CLI/TUI fallback later

## Planned stack

- Django backend and web UI
- PostgreSQL database
- Docker Compose deployment
- Future Python CLI/TUI sharing the same backend logic

## Repository layout

```text
backend/             Django project and canteen app
compose.yaml         Local/self-hosted Docker Compose stack
docs/                Design notes, deployment guide, and MVP scope
.env.example         Example environment variables
```

## Deployment

See [docs/initial-deployment.md](docs/initial-deployment.md) for first-deploy setup, database migrations, and Django admin account creation.

Quick start:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Development status

Prototype planning/skeleton stage.
