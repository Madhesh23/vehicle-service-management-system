import functools
import re
import secrets
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import abort, flash, g, redirect, session, url_for

STATUSES = ["Booked", "In Progress", "Completed", "Delivered"]
NEXT_STATUS = {"Booked": "In Progress", "In Progress": "Completed", "Completed": "Delivered"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[0-9]{10,15}$")
VEHICLE_RE = re.compile(r"^[A-Z0-9-]{4,15}$")

BOOKING_SELECT = """
SELECT b.booking_id, b.service_date, b.status, b.remarks, b.vehicle_id, b.service_id,
       v.vehicle_number, v.brand, v.model, v.user_id,
       s.service_name, s.charge,
       u.name AS customer_name, u.phone AS customer_phone,
       bl.bill_id
FROM bookings b
JOIN vehicles v ON v.vehicle_id = b.vehicle_id
JOIN users u ON u.user_id = v.user_id
JOIN services s ON s.service_id = b.service_id
LEFT JOIN bills bl ON bl.booking_id = b.booking_id
"""


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*a, **kw)
    return wrapped


def role_required(role):
    def deco(view):
        @functools.wraps(view)
        def wrapped(*a, **kw):
            if g.user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if g.user["role"] != role:
                abort(403)
            return view(*a, **kw)
        return wrapped
    return deco


customer_required = role_required("customer")
admin_required = role_required("admin")


def clean(value, maxlen=None):
    value = (value or "").strip()
    return value[:maxlen] if maxlen else value


def parse_money(raw, allow_zero=True):
    try:
        val = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        return None
    if not val.is_finite() or val < 0 or (val == 0 and not allow_zero) or val > Decimal("99999999"):
        return None
    return float(round(val, 2))


def parse_int(raw, minimum=0, maximum=1_000_000):
    try:
        val = int(str(raw).strip())
    except ValueError:
        return None
    return val if minimum <= val <= maximum else None


def parse_date(raw):
    try:
        return datetime.strptime((raw or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_vehicle_number(raw):
    return re.sub(r"\s+", "", (raw or "").upper())


def today():
    return date.today()


def generate_bill(db, booking_id):
    """Create the bill for a booking: service charge + parts total."""
    if db.one("SELECT bill_id FROM bills WHERE booking_id=%s", (booking_id,)):
        return
    charge = float(db.scalar(
        "SELECT s.charge FROM bookings b JOIN services s ON s.service_id=b.service_id "
        "WHERE b.booking_id=%s", (booking_id,)))
    parts_total = 0.0
    for p in db.all("SELECT quantity, unit_price FROM booking_parts WHERE booking_id=%s", (booking_id,)):
        parts_total += float(p["unit_price"]) * int(p["quantity"])
    parts_total = round(parts_total, 2)
    total = round(charge + parts_total, 2)
    db.run("INSERT INTO bills (booking_id, service_charge, parts_total, total_amount, bill_date) "
           "VALUES (%s,%s,%s,%s,%s)",
           (booking_id, charge, parts_total, total, today().isoformat()))
