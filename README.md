# Vastra Care / Fabric Care Website

Django **contact-first** landing page: phone, WhatsApp, email, and a public enquiry form. Content is managed in **Django admin** (`/admin/`).

## CMS (landing page from admin)

After `migrate`, open **`/admin/`** — the index title is **Landing page management**. Key models:

- **Site settings** — brand, SEO, header CTA (`nav_contact_label` / `nav_contact_url`), hero timing and **auto-advance**, footer copy, contact & social links (`maps_url` for Google Maps), **Website appearance** (colours, fonts, spacing, container width), header/footer colours, logo max height, sticky header.
- **Landing page sections** — drag to **reorder** the main blocks (About → Services → … → Contact), toggle visibility, optional per-section background colour/image.
- **Navigation links**, **Hero slides**, **Services**, **Difference points**, **Process steps**, **Testimonials** — **drag-and-drop order** (django-admin-sortable2), enable/disable, CRUD.
- **About section** (singleton) — optional CTA button and section colours; **About features** can use icon or uploaded image.
- **Call to action** — optional second button, background colour/image; hide with **Is visible**.
- **Section headings** — eyebrow/title/subheading per block; **Is visible** hides the heading block only.

Hero overlay strength is controlled per slide (**overlay opacity**). Service cards support optional **category**, **price** (prefix/suffix/amount), and **booking** link.

**Production media on Render:** the app disk is ephemeral; configure **S3** (or Cloudinary) for `DEFAULT_FILE_STORAGE` if uploads must survive restarts — see Django 4.2 `STORAGES` docs.

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
2. In [Render](https://render.com), **New → Blueprint** and connect your repo (uses `render.yaml`), **or** create a **Web Service** manually:
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
| `BREVO_API_KEY` | Brevo **API key** (`xkeysib-…`) — recommended on Render ([SMTP & API](https://app.brevo.com/settings/keys/api)) |
| `EMAIL_HOST_USER` | Brevo **SMTP login** (`xxxx@smtp-brevo.com`) if not using API key |
| `BREVO_SMTP_KEY` | Brevo **SMTP password** (not the API key) when using SMTP relay |
| `DEFAULT_FROM_EMAIL` | **Verified sender** in Brevo (e.g. your Gmail — not `@smtp-brevo.com`) |
| Brevo IP security | Turn **off** strict IP allowlisting for Render, or outbound mail may fail |
| Other email vars | `EMAIL_HOST=smtp-relay.brevo.com`, port `587`, TLS — preset in `render.yaml` |

After deploy, open **Render → Logs** and search for `Email configuration (Render build)` to confirm mail is configured. For contact tests, use `python manage.py send_test_email you@example.com` locally or configure Brevo and submit the site enquiry form.

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
