#!/usr/bin/env sh
set -eu

if [ "${DJANGO_DEBUG:-0}" = "0" ]; then
  case "${DJANGO_SECRET_KEY:-}" in
    ""|change-me|dev-only-insecure-secret-key|replace-with-*)
      echo "DJANGO_SECRET_KEY must be a long random value when DJANGO_DEBUG=0." >&2
      exit 1
      ;;
  esac
  if [ "${#DJANGO_SECRET_KEY}" -lt 50 ]; then
    echo "DJANGO_SECRET_KEY must contain at least 50 characters when DJANGO_DEBUG=0." >&2
    exit 1
  fi
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${CANTEEN_SHOW_DEPLOY_HINT:-1}" != "0" ]; then
  cat <<'EOF'

============================================================
Usask IEEE Canteen deployment reminder
============================================================
Database migrations and static collection run automatically before Gunicorn starts.
To verify migrations or create the first admin, run:

  docker compose exec web python manage.py showmigrations
  docker compose exec web python manage.py createsuperuser

Then open:

  http://<server-ip-or-domain>:8000/admin/

Full guide: docs/initial-deployment.md
Set CANTEEN_SHOW_DEPLOY_HINT=0 to hide this reminder.
============================================================

EOF
fi

exec "$@"
