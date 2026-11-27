# Vehicle Service Management System

Flask + MySQL (Bootstrap, Jinja2). Customers register vehicles, book services, track status and view bills.
Administrators manage bookings, parts, services and billing.

## 1. Install (once)
```
cd vehicle_service
python -m venv venv
venv\Scripts\activate          (Windows)      source venv/bin/activate   (Linux/macOS)
pip install -r requirements.txt
```
(Or just double-click `run.bat` on Windows / run `./run.sh` on Linux/macOS: it does steps 1 and 3.)

## 2. Database
**Option A - MySQL (as in the project report)**
1. Install MySQL and make sure it is running.
2. Open `config.py` and set `MYSQL_USER` / `MYSQL_PASSWORD` (or set them as environment variables).
3. That's it - the database `vehicle_service_db` and all tables are created automatically on first run.

**Option B - no MySQL (quick demo)**: run with `DB_TYPE=sqlite` (Windows: `set DB_TYPE=sqlite`).
Default `DB_TYPE=auto` tries MySQL first and falls back to SQLite if MySQL is not reachable.
The console shows which database is in use ("Database : MYSQL" or "SQLITE").

## 3. Run
```
python app.py
```
Open **http://localhost:5000**

| Role | Login |
|---|---|
| Administrator | admin@service.com / admin123 |
| Customer | click *Register* and create one |

(Change the admin login with ADMIN_EMAIL / ADMIN_PASSWORD before the first run.)
Sample services and spare parts are added on the first run.

## 4. Run the automated tests
```
python -m unittest tests.test_app -v
```

## 5. Share it / make it public
* Same Wi-Fi/LAN: `set HOST=0.0.0.0` then `python app.py`, and open `http://<your-PC-IP>:5000` on another device.
* Temporary public link for a demo: install ngrok and run `ngrok http 5000`.
* Permanent hosting: PythonAnywhere (free tier, includes MySQL). Upload the folder, install requirements,
  set MYSQL_* variables, point the WSGI file at `app:create_app()`. Set a real `SECRET_KEY` and change the admin password.

## Project structure
```
app.py            application factory + run
config.py         settings
db.py             database layer (MySQL / SQLite), schema, first-run seed
utils.py          validators, decorators, billing
routes/           auth.py  customer.py  admin.py
templates/        Jinja2 pages (customer/, admin/)
static/           style.css, app.js
schema_mysql.sql  reference MySQL schema
tests/test_app.py 30 automated tests
```
