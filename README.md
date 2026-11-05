# Vastra Care / Fabric Care Website

Django landing page with customer booking, Razorpay payments, staff portal, and admin content.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed
python manage.py runserver
```

## Deploy on Render

1. Push this repo to GitHub (see below).
2. In [Render](https://render.com), **New → Blueprint** and connect `Poonghuzhali/fabric_care` (uses `render.yaml`), **or** create a **Web Service** manually:
   - **Build command:** `./build.sh`
   - **Start command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
3. Add a **PostgreSQL** database (recommended). Set `DATABASE_URL` from the database (included in Blueprint).
4. Set environment variables in Render (do **not** commit `.env`):

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | long random string (Render can generate) |
| `DEBUG` | `false` |
| `SITE_URL` | `https://your-app.onrender.com` |
| `ALLOWED_HOSTS` | `your-app.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.onrender.com` |
| `GOOGLE_MAPS_API_KEY` | your key (restrict by Render URL) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | test or live keys |
| Gmail SMTP vars | same as local `.env` |

5. After first deploy, open the site and sign in to **Staff portal** (`/portal/login/`) with the account created on migrate (`admin@serviceportal.com` — password set in `portal/accounts.py`; change for production).

**Note:** User-uploaded media on Render’s free disk is ephemeral. For production, use S3 or similar for `MEDIA_ROOT`.

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Fabric Care Django site"
git branch -M main
git remote add origin https://github.com/Poonghuzhali/fabric_care.git
git push -u origin main
```
