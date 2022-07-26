"""App config objects"""
import os


# pylint: disable=R0903
class Config:
    """Base config class"""

    DEBUG = True
    TESTING = False

    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ADMIN_KEY = os.environ.get("ADMIN_KEY")

    LANGUAGES = {
        "en": "English",
        "fr": "français",
    }

    MIMETYPES_ALLOWED = [
        "image/jpeg",
        "image/png",
        "image/svg+xml",
        "image/webp",
        "image/bmp",
        "image/tiff",
    ]

    MAX_CONTENT_LENGTH = 32 * 1024 * 1024

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DICT_LOGGER = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": ("%(asctime)s [%(levelname)s] [%(name)s] | %(message)s")
            },
        },
    }


# pylint: disable=R0903
class ProductionConfig(Config):
    """Config class for a production environment"""

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = "sqlite:////usr/paperglobe_web/db/sqlite.db"

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://redis:6379"
    )
    REDIS_BROKER_URL = os.environ.get("REDIS_BROKER_URL", "redis://redis:6379")


# pylint: disable=R0903
class DevelopmentConfig(Config):
    """Config class for a dev environment"""

    DEVELOPMENT = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "sqlite:////usr/paperglobe_web/db/sqlite.db"

    CELERY_BROKER_URL = "redis://redis:6379"
    CELERY_RESULT_BACKEND = "redis://redis:6379"
    REDIS_BROKER_URL = "redis://redis:6379"


# pylint: disable=R0903
class TestingConfig(Config):
    """Config class for a testing environment"""

    TESTING = True
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_POOL_SIZE = None
    SQLALCHEMY_POOL_TIMEOUT = None

    CELERY_BROKER_URL = "redis://redis:6379"
    CELERY_RESULT_BACKEND = "redis://redis:6379"
    REDIS_BROKER_URL = "redis://redis:6379"
