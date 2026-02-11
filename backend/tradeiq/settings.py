# TradeIQ - Design Document v3.0
# Django 5 + DRF + Channels; DB: Supabase (PostgreSQL)
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR.parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "channels",
    "market",
    "behavior",
    "content",
    "agents",
    "chat",
    "demo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tradeiq.urls"
ASGI_APPLICATION = "tradeiq.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tradeiq.wsgi.application"

# Database: Supabase (PostgreSQL). Get the exact URI from dashboard: Connect -> URI (Session or Direct).
# If you get ParseError: URL-encode special characters in the password (@ -> %40, # -> %23, : -> %3A, / -> %2F).
_default_db = {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
if os.environ.get("DATABASE_URL"):
    try:
        import dj_database_url
        _url = os.environ.get("DATABASE_URL")
        try:
            DATABASES = {
                "default": dj_database_url.config(
                    default=_url,
                    conn_max_age=600,
                    conn_health_checks=True,
                )
            }
        except Exception as parse_err:
            import sys
            error_msg = str(parse_err).lower()
            if "parseerror" in type(parse_err).__name__.lower() or "not a valid url" in error_msg or "port could not be cast" in error_msg:
                print("DATABASE_URL parse error (often due to special chars in password).", file=sys.stderr)
                print("URL-encode the password in .env: @ -> %40, # -> %23, : -> %3A, / -> %2F", file=sys.stderr)
                print(f"Error: {parse_err}", file=sys.stderr)
                DATABASES = {"default": _default_db}
            else:
                raise
    except ImportError:
        DATABASES = {"default": _default_db}
else:
    DATABASES = {"default": _default_db}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "tradeiq.middleware.supabase_auth.SupabaseJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "tradeiq.exceptions.custom_exception_handler",
}

# Supabase Auth (Phase 6)
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")

# Google OAuth app settings (used by Supabase Google provider setup)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_CALLBACK_URL = os.environ.get("CALLBACK_URL", "")

# CORS: Allow Next.js frontend (Phase 4)
# Set CORS_ALLOWED_ORIGINS env var for cloud deployment (comma-separated)
# e.g. CORS_ALLOWED_ORIGINS=https://tradeiq.vercel.app,http://localhost:3000
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all origins in debug/demo mode

# Bluesky (Appendix B) - from .env
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

# Fixtures for demo scenarios (Section 10, 14)
FIXTURE_DIRS = [os.path.join(BASE_DIR, "fixtures")]

# Channels – prefer Redis (Upstash), fall back to in-memory
_redis_url = os.environ.get("REDIS_URL", "")
if _redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [_redis_url],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
