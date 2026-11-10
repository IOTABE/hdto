from .base import *  # noqa: F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME"),  # noqa: F405
        "USER": env("DB_USER"),  # noqa: F405
        "PASSWORD": env("DB_PASSWORD"),  # noqa: F405
        "HOST": env("DB_HOST", default="host.docker.internal"),  # noqa: F405
        "PORT": env("DB_PORT", default="5434"),  # noqa: F405
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": env("DB_SSLMODE", default="prefer")},  # noqa: F405
    }
}

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")  # noqa: F405

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
}

if not FIELD_ENCRYPTION_KEY:  # noqa: F405
    raise RuntimeError("FIELD_ENCRYPTION_KEY é obrigatória em produção")
