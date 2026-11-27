"""Vehicle Service Management System  -  Flask application.

Run:   python app.py        then open  http://127.0.0.1:5000
"""
import os
import secrets

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for

import config
import db as database
from utils import STATUSES, csrf_token


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_object(config)
    if test_config:
        app.config.update(test_config)

    # persistent secret key (so logins survive a restart)
    if not app.config.get("SECRET_KEY"):
        key_file = os.path.join(app.instance_path, "secret.key")
        if not os.path.exists(key_file):
            with open(key_file, "w") as fh:
                fh.write(secrets.token_hex(32))
        app.config["SECRET_KEY"] = open(key_file).read().strip()
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    database.setup_database(app)
    app.teardown_appcontext(database.close_db)

    from routes import admin, auth, customer
    app.register_blueprint(auth.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(admin.bp)

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        uid = session.get("user_id")
        if uid:
            g.user = database.get_db().one("SELECT * FROM users WHERE user_id=%s", (uid,))
            if g.user is None:
                session.clear()
        if request.method == "POST":
            sent = request.form.get("csrf_token", "")
            if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
                flash("Your session expired. Please try again.", "warning")
                return redirect(request.referrer or url_for("auth.index"))

    @app.context_processor
    def inject():
        return {"csrf_token": csrf_token, "STATUSES": STATUSES, "current_user": g.get("user")}

    @app.template_filter("money")
    def money(value):
        try:
            return "\u20b9{:,.2f}".format(float(value))
        except (TypeError, ValueError):
            return "\u20b90.00"

    @app.template_filter("dfmt")
    def dfmt(value):
        s = str(value)[:10]
        try:
            y, m, d = s.split("-")
            return "%s-%s-%s" % (d, m, y)
        except ValueError:
            return s

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="You do not have permission to open this page."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="The page you are looking for was not found."), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500

    return app


if __name__ == "__main__":
    application = create_app()
    print("\n  Vehicle Service Management System")
    print("  Database : %s" % application.config["DB_KIND"].upper())
    print("  Open     : http://%s:%s\n" % ("localhost" if config.HOST in ("127.0.0.1", "0.0.0.0") else config.HOST, config.PORT))
    application.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
