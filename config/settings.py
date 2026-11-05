import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

SECRET_KEY = os.environ.get("SECRET_KEY", "iron-meka-dev-key-change-before-production")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")

_allowed = os.environ.get("ALLOWED_HOSTS", "").strip()
ALLOWED_HOSTS = [host.strip() for host in _allowed.split(",") if host.strip()] or ["*"]

_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf.split(",") if origin.strip()]
_site_url_early = os.environ.get("SITE_URL", "").strip()
if _site_url_early and _site_url_early not in CSRF_TRUSTED_ORIGINS and _site_url_early.startswith("http"):
    CSRF_TRUSTED_ORIGINS.append(_site_url_early)
if _render_host:
    _render_origin = f"https://{_render_host}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)

CSRF_TRUSTED_ORIGINS = sorted({origin.rstrip("/") for origin in CSRF_TRUSTED_ORIGINS if origin})

CSRF_FAILURE_VIEW = "config.views.csrf_failure"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "care.apps.CareConfig",
    "portal.apps.PortalConfig",
]

AUTHENTICATION_BACKENDS = [
    "portal.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/account/"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

if dj_database_url and os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email — use console in dev; set SMTP env vars in production.
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
# Render demo: use Razorpay test keys when env vars are not set (override via Environment for live keys).
if os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip() and not (
    RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET
):
    RAZORPAY_KEY_ID = "rzp_test_TwPx3y5C93Wi2O"
    RAZORPAY_KEY_SECRET = "qlgLhbbMdj6Jp8pdVc71QjDA"
PAYMENT_SKIP_VERIFY = os.environ.get("PAYMENT_SKIP_VERIFY", "").lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "hello@vastracare.in")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").replace(" ", "")
if not EMAIL_HOST_PASSWORD:
    EMAIL_HOST_PASSWORD = os.environ.get("BREVO_SMTP_KEY", "").strip()
if not EMAIL_HOST_PASSWORD:
    EMAIL_HOST_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() in ("1", "true", "yes")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "30"))

# Gmail: port 587 + TLS, or port 465 + SSL — not both.
if EMAIL_USE_SSL:
    EMAIL_USE_TLS = False

if EMAIL_HOST and EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

if EMAIL_HOST_USER and DEFAULT_FROM_EMAIL == "hello@vastracare.in":
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    SERVER_EMAIL = EMAIL_HOST_USER

_on_render = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _on_render:
    if not EMAIL_HOST:
        EMAIL_HOST = "smtp-relay.brevo.com"
    if EMAIL_HOST and EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_CONFIGURED = bool(
    EMAIL_HOST
    and EMAIL_HOST_USER
    and EMAIL_HOST_PASSWORD
    and EMAIL_HOST_USER != "your.name@gmail.com"
    and "your-16-char" not in EMAIL_HOST_PASSWORD
    and EMAIL_HOST_PASSWORD != "your-brevo-smtp-key"
)
