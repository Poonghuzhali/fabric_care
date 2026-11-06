#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py report_email_config
python manage.py seed
python manage.py collectstatic --noinput

python - <<'PY'
import os

on_render = bool(os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip())

email_user = os.environ.get("EMAIL_HOST_USER", "").strip()
email_pass = (
    os.environ.get("EMAIL_HOST_PASSWORD", "").strip()
    or os.environ.get("BREVO_SMTP_KEY", "").strip()
    or os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
)
brevo_api = os.environ.get("BREVO_API_KEY", "").strip()

if on_render and brevo_api:
    print("Brevo API key set on Render. Contact form notifications can use Brevo HTTP API.")
elif on_render and (not email_user or not email_pass):
    print(
        "BUILD WARNING: Outbound email may not work until you set "
        "BREVO_API_KEY (xkeysib-…) or EMAIL_HOST_USER + BREVO_SMTP_KEY on Render."
    )
elif on_render:
    host = os.environ.get("EMAIL_HOST", "smtp-relay.brevo.com")
    print(f"SMTP configured on Render via {host} (login: {email_user}).")
PY
