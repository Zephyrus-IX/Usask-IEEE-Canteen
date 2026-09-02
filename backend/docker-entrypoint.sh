#!/usr/bin/env sh
set -eu

if [ "${CANTEEN_SHOW_DEPLOY_HINT:-1}" != "0" ]; then
  cat <<'EOF'

============================================================
Usask IEEE Canteen deployment reminder
============================================================
If this is the first time this stack has been started, run:

  docker compose exec web python manage.py migrate
  docker compose exec web python manage.py createsuperuser

Then open:

  http://<server-ip-or-domain>:8000/admin/

Full guide: docs/initial-deployment.md
Set CANTEEN_SHOW_DEPLOY_HINT=0 to hide this reminder.
============================================================

EOF
fi

exec "$@"
