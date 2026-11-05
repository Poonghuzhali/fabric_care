#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
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
PY
