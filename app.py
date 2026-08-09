from flask import Flask, render_template, request, redirect, flash, jsonify, abort
import smtplib
from email.mime.text import MIMEText
import os
import sqlite3
import uuid
import json
from datetime import datetime

app = Flask(__name__)
# Read secret key from environment, with a safe default for local testing
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "zakmolan_secret_2026")

# Email configuration — set these as environment variables in production
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS", "zakmolan@gmail.com")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Must be set in the environment

# Admin key for viewing donations (set in env for quick admin access)
ADMIN_KEY = os.environ.get("ADMIN_KEY")

DB_PATH = os.environ.get("DONATIONS_DB", "donations.db")

# Initialize a simple SQLite DB for donation records (kept for records/administration)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id TEXT PRIMARY KEY,
            provider TEXT,
            tx_ref TEXT,
            phone TEXT,
            amount TEXT,
            currency TEXT,
            status TEXT,
            message TEXT,
            donor_email TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def save_donation_record(rec):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO donations (id, provider, tx_ref, phone, amount, currency, status, message, donor_email, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            rec.get("id"),
            rec.get("provider"),
            rec.get("tx_ref"),
            rec.get("phone"),
            rec.get("amount"),
            rec.get("currency"),
            rec.get("status"),
            rec.get("message"),
            rec.get("donor_email", ""),
            rec.get("created_at"),
        ),
    )
    conn.commit()
    conn.close()


def update_donation_status(tx_ref, status, message=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if message is None:
        c.execute("UPDATE donations SET status = ? WHERE tx_ref = ?", (status, tx_ref))
    else:
        c.execute("UPDATE donations SET status = ?, message = ? WHERE tx_ref = ?", (status, message, tx_ref))
    conn.commit()
    conn.close()


def get_donation_by_tx(tx_ref):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, provider, tx_ref, phone, amount, currency, status, message, donor_email, created_at FROM donations WHERE tx_ref = ?", (tx_ref,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    keys = ["id", "provider", "tx_ref", "phone", "amount", "currency", "status", "message", "donor_email", "created_at"]
    return dict(zip(keys, row))


def list_donations(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, provider, tx_ref, phone, amount, currency, status, message, donor_email, created_at FROM donations ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    keys = ["id", "provider", "tx_ref", "phone", "amount", "currency", "status", "message", "donor_email", "created_at"]
    return [dict(zip(keys, r)) for r in rows]


def send_email(subject, recipient_email, message):
    if not YOUR_PASSWORD:
        print("Email error: EMAIL_PASSWORD environment variable is not set")
        return False

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = YOUR_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(YOUR_EMAIL, YOUR_PASSWORD)
            # Send to site owner
            msg["To"] = YOUR_EMAIL
            server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
            # Optionally send to donor if recipient_email provided and different
            if recipient_email and recipient_email != YOUR_EMAIL:
                msg["To"] = recipient_email
                server.sendmail(YOUR_EMAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print("Email error:", e)
        return False


# -------------------------
# Routes (payments removed)
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        if send_email(name, email, message):
            flash("✅ Message sent! We'll reply to you soon at %s" % YOUR_EMAIL)
        else:
            flash("❌ Error sending message. Please call 256 742956448")
        return redirect("/contact")
    return render_template("contact.html")


@app.route("/donate", methods=["GET", "POST"])
def donate():
    # Donations are temporarily disabled. Redirect to home with a notice.
    flash("Donations are temporarily paused. Please contact us at 256 742956448 or zakmolan@gmail.com")
    return redirect("/")


# -------------------------
# Admin endpoints (simple, protected by ADMIN_KEY env var)
# -------------------------

@app.route('/admin/donations')
def admin_donations():
    key = request.args.get('admin_key')
    if not ADMIN_KEY or key != ADMIN_KEY:
        abort(403)
    donations = list_donations(limit=500)
    return jsonify({'success': True, 'count': len(donations), 'donations': donations})


@app.route('/admin/donation/<tx_ref>')
def admin_view_donation(tx_ref):
    key = request.args.get('admin_key')
    if not ADMIN_KEY or key != ADMIN_KEY:
        abort(403)
    d = get_donation_by_tx(tx_ref)
    if not d:
        return jsonify({'success': False, 'message': 'not found'}), 404
    return jsonify({'success': True, 'donation': d})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
