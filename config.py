"""Configuration. Every value can be overridden with an environment variable."""
import os

# DB_TYPE: "mysql" | "sqlite" | "auto"
#   auto   -> use MySQL if it can be reached, otherwise fall back to SQLite
DB_TYPE = os.environ.get("DB_TYPE", "auto")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")      # <- put your MySQL password here or in the env
MYSQL_DB = os.environ.get("MYSQL_DB", "vehicle_service_db")

SQLITE_PATH = os.environ.get("SQLITE_PATH", "")             # empty = instance/vehicle_service.db

HOST = os.environ.get("HOST", "127.0.0.1")                  # use 0.0.0.0 to open it to your network
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

SECRET_KEY = os.environ.get("SECRET_KEY", "")               # empty = generated once and saved in instance/

# Default administrator, created only on the very first run
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Administrator")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@service.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
