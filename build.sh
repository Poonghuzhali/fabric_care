#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py ensure_portal_admin --reset-password
python manage.py seed
python manage.py collectstatic --noinput

python - <<'PY'
import os
import sys

on_render = bool(os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip())
key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
if on_render and (not key_id or not secret):
    print(
        "BUILD WARNING: Razorpay is not configured on Render. "
        "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in Environment, then redeploy."
    )
elif on_render:
    mode = "test" if key_id.startswith("rzp_test_") else "live"
    print(f"Razorpay configured on Render ({mode} mode). Online booking payments enabled.")

email_user = os.environ.get("EMAIL_HOST_USER", "").strip()
email_pass = (
    os.environ.get("EMAIL_HOST_PASSWORD", "").strip()
    or os.environ.get("BREVO_SMTP_KEY", "").strip()
    or os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
)
brevo_api = os.environ.get("BREVO_API_KEY", "").strip()
if on_render and brevo_api:
    print("Brevo API key set on Render. Booking confirmation emails use Brevo HTTP API.")
elif on_render and (not email_user or not email_pass):
    print(
        "BUILD WARNING: Booking confirmation email will NOT send until you set "
        "BREVO_API_KEY (xkeysib-…) or EMAIL_HOST_USER + BREVO_SMTP_KEY on Render."
    )
elif on_render:
    host = os.environ.get("EMAIL_HOST", "smtp-relay.brevo.com")
    print(f"SMTP configured on Render via {host} (login: {email_user}). Booking emails enabled.")
PY
