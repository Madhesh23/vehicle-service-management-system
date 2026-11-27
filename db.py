"""Database layer.

Uses plain parameterized SQL (no string formatting of user input -> no SQL injection).
The same queries run on MySQL (PyMySQL) and SQLite; only the connection and the
CREATE TABLE statements differ.
"""
import os
import sqlite3
from collections import namedtuple

from flask import current_app, g
from werkzeug.security import generate_password_hash

Result = namedtuple("Result", "lastrowid rowcount")


class Database:
    def __init__(self, conn, kind):
        self.conn, self.kind = conn, kind

    def _sql(self, sql):
        return sql.replace("%s", "?") if self.kind == "sqlite" else sql

    def all(self, sql, args=()):
        if self.kind == "sqlite":
            cur = self.conn.execute(self._sql(sql), tuple(args))
            rows = [dict(r) for r in cur.fetchall()]
            cur.close()
            return rows
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(args))
            return list(cur.fetchall())

    def one(self, sql, args=()):
        rows = self.all(sql, args)
        return rows[0] if rows else None

    def scalar(self, sql, args=(), default=0):
        row = self.one(sql, args)
        if not row:
            return default
        val = list(row.values())[0]
        return default if val is None else val

    def run(self, sql, args=()):
        if self.kind == "sqlite":
            cur = self.conn.execute(self._sql(sql), tuple(args))
            res = Result(cur.lastrowid, cur.rowcount)
            cur.close()
            return res
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(args))
            return Result(cur.lastrowid, cur.rowcount)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


# ----------------------------------------------------------------- schemas
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone TEXT,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer','admin'))
);
CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  vehicle_number TEXT NOT NULL UNIQUE, brand TEXT NOT NULL, model TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS services (
  service_id INTEGER PRIMARY KEY AUTOINCREMENT,
  service_name TEXT NOT NULL UNIQUE, charge NUMERIC NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
  booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
  service_id INTEGER NOT NULL REFERENCES services(service_id),
  service_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Booked'
    CHECK (status IN ('Booked','In Progress','Completed','Delivered')),
  remarks TEXT
);
CREATE TABLE IF NOT EXISTS spare_parts (
  part_id INTEGER PRIMARY KEY AUTOINCREMENT,
  part_name TEXT NOT NULL UNIQUE, price NUMERIC NOT NULL,
  stock_quantity INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS booking_parts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
  part_id INTEGER NOT NULL REFERENCES spare_parts(part_id),
  quantity INTEGER NOT NULL, unit_price NUMERIC NOT NULL
);
CREATE TABLE IF NOT EXISTS bills (
  bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(booking_id) ON DELETE CASCADE,
  service_charge NUMERIC NOT NULL, parts_total NUMERIC NOT NULL,
  total_amount NUMERIC NOT NULL, bill_date TEXT NOT NULL
);
"""


def _mysql_statements():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_mysql.sql")
    text = "\n".join(l for l in open(path, encoding="utf-8").read().splitlines()
                     if not l.strip().startswith("--"))
    stmts = [s.strip() for s in text.split(";") if s.strip()]
    return [s for s in stmts if not s.upper().startswith(("CREATE DATABASE", "USE "))]


SAMPLE_SERVICES = [("General Service", 1500), ("Oil Change", 800), ("Wheel Alignment", 600),
                   ("Brake Service", 1200), ("AC Service", 1800), ("Car Wash", 300)]
SAMPLE_PARTS = [("Engine Oil (1 L)", 450, 50), ("Oil Filter", 250, 40), ("Air Filter", 300, 30),
                ("Brake Pad Set", 1400, 20), ("Spark Plug", 180, 60), ("Wiper Blade", 220, 25),
                ("Coolant (1 L)", 350, 30), ("Battery", 4500, 8)]


# ------------------------------------------------------------ connections
def connect(app, kind):
    if kind == "sqlite":
        conn = sqlite3.connect(app.config["SQLITE_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return Database(conn, "sqlite")
    import pymysql
    from pymysql.constants import CLIENT
    conn = pymysql.connect(
        host=app.config["MYSQL_HOST"], port=int(app.config["MYSQL_PORT"]),
        user=app.config["MYSQL_USER"], password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"], charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, client_flag=CLIENT.FOUND_ROWS,
        autocommit=False)
    return Database(conn, "mysql")


def _create_mysql_database(app):
    import pymysql
    conn = pymysql.connect(host=app.config["MYSQL_HOST"], port=int(app.config["MYSQL_PORT"]),
                           user=app.config["MYSQL_USER"], password=app.config["MYSQL_PASSWORD"])
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4"
                        % app.config["MYSQL_DB"].replace("`", ""))
        conn.commit()
    finally:
        conn.close()


def setup_database(app):
    """Pick the backend, create tables, and seed data on the very first run."""
    wanted = str(app.config["DB_TYPE"]).lower()
    kind = None
    if wanted in ("mysql", "auto"):
        try:
            _create_mysql_database(app)
            connect(app, "mysql").close()
            kind = "mysql"
        except Exception as exc:
            if wanted == "mysql":
                raise RuntimeError(
                    "Could not connect to MySQL (%s). Check MYSQL_USER / MYSQL_PASSWORD in "
                    "config.py and that the MySQL server is running." % exc)
            print("[!] MySQL not reachable (%s)\n    Falling back to SQLite. "
                  "Set DB_TYPE=mysql to require MySQL." % exc)
    if kind is None:
        kind = "sqlite"
        if not app.config["SQLITE_PATH"]:
            app.config["SQLITE_PATH"] = os.path.join(app.instance_path, "vehicle_service.db")
    app.config["DB_KIND"] = kind

    db = connect(app, kind)
    try:
        if kind == "sqlite":
            db.conn.executescript(SQLITE_SCHEMA)
        else:
            for stmt in _mysql_statements():
                db.run(stmt)
            db.commit()
        if db.scalar("SELECT COUNT(*) FROM users") == 0:
            db.run("INSERT INTO users (name,email,phone,password,role) VALUES (%s,%s,%s,%s,'admin')",
                   (app.config["ADMIN_NAME"], app.config["ADMIN_EMAIL"].lower(), "",
                    generate_password_hash(app.config["ADMIN_PASSWORD"])))
            for n, c in SAMPLE_SERVICES:
                db.run("INSERT INTO services (service_name,charge) VALUES (%s,%s)", (n, c))
            for n, p, s in SAMPLE_PARTS:
                db.run("INSERT INTO spare_parts (part_name,price,stock_quantity) VALUES (%s,%s,%s)", (n, p, s))
            db.commit()
            print("[*] First run: created admin account %s" % app.config["ADMIN_EMAIL"])
    finally:
        db.close()


def get_db():
    if "db" not in g:
        g.db = connect(current_app, current_app.config["DB_KIND"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
