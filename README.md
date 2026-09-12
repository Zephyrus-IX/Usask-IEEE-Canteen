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
.env                 Dockhand environment template with placeholder values
canteen              Deployment helper for install/update/admin commands
```

## Deployment

See [docs/initial-deployment.md](docs/initial-deployment.md) for first-deploy setup, database migrations, and Django admin account creation.

Future work, including encrypted PostgreSQL exports to removable USB storage, is tracked in [docs/roadmap.md](docs/roadmap.md).

Quick start for laptop/LAN testing:

```bash
./canteen install --lan
./canteen logs --lan
./canteen createsuperuser --lan
```

The LAN override publishes port `8000` only for pre-tunnel testing. The base Compose file keeps Gunicorn internal so a future `cloudflared` service can reach `web:8000` without creating a direct public origin bypass.

Use `./canteen update --lan` for normal laptop/LAN updates. It pulls the latest code and rebuilds without deleting the PostgreSQL volume. Only use `./canteen reset-test-db --lan` when you intentionally want to wipe local test data.

## Development status

Prototype planning/skeleton stage.
