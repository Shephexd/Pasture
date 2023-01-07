import os
import re


def parse_database_url(db_url):
    regex = re.compile(DB_URL_PATTERN)
    matched = regex.match(db_url)
    if not matched:
        return {}
    db_setting = matched.groupdict()
    db_setting["ENGINE"] = DB_TYPE_ENGINE_MAP[db_setting.pop("DB_TYPE")]
    return db_setting


DB_URL_PATTERN = "(?P<DB_TYPE>\w+):\/\/(?P<USER>[\w_\-0-9]+):(?P<PASSWORD>[.\w+]+)@(?P<HOST>[-.\w+]+):(?P<PORT>[0-9]+)\/(?P<NAME>\w+)"
DB_TYPE_ENGINE_MAP = {"postgres": "django.db.backends.postgresql_psycopg2"}

ALLOWED_HOSTS = os.getenv("HOSTNAME", "").split(",")

DEBUG = False
if os.getenv("DEBUG", False):
    DEBUG = True

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
SECRET_KEY = os.getenv("SECRET_KEY", "SECRET_KEY")
DEFAULT_DB_URL = os.getenv("DATABASE_URL", "")
DEFAULT_DB = parse_database_url(DEFAULT_DB_URL)
DATABASES = {"default": DEFAULT_DB}
