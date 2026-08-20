# Usask IEEE Canteen

A self-hosted Docker app to manage and track inventory, in-person sales, student tabs, prepaid balances, restocks, and expenses for the Usask IEEE student branch canteen.

## Project goals

- Exec-facilitated in-person sales only
- Every sale must be attached to an active student tab
- Student tabs are created by an admin/IEEE exec
- Optional prepaid student balances
- IEEE member and non-member pricing
- Inventory automatically decreases on completed sales
- Restocks are manually entered and increase inventory
- Restock GST/PST/LST tracking with configurable tax rates
- CSV exports for sales, balances, restocks, inventory, and student tabs
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
docs/                Design notes and MVP scope
.env.example         Example environment variables
```

## Development status

Prototype planning/skeleton stage.
