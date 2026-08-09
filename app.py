from flask import Flask, render_template, request, redirect, flash, jsonify
import smtplib
from email.mime.text import MIMEText
import os
import requests
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

# Mobile money config — provider-specific credentials should be set as env vars
# MTN example env vars: MTN_API_URL, MTN_USER, MTN_API_KEY, MTN_API_SECRET
# AIRTEL example env vars: AIRTEL_API_URL, AIRTEL_API_KEY, AIRTEL_SECRET

DB_PATH = os.environ.get("DONATIONS_DB", "donations.db")

# Initialize a simple SQLite DB for donation records
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
        "INSERT OR REPLACE INTO donations (id, provider, tx_ref, phone, amount, currency, status, message, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            rec.get("id"),
            rec.get("provider"),
            rec.get("tx_ref"),
            rec.get("phone"),
            rec.get("amount"),
            rec.get("currency"),
            rec.get("status"),
            rec.get("message"),
            rec.get("created_at"),
        ),
    )
    conn.commit()
    conn.close()


def send_email(name, email, message):
    if not YOUR_PASSWORD:
        print("Email error: EMAIL_PASSWORD environment variable is not set")
        return False

    subject = f"New Contact from Zakmolanitechsolutions - {name}"
    body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = YOUR_EMAIL
    msg["To"] = YOUR_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(YOUR_EMAIL, YOUR_PASSWORD)
            server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
        return True
    except Exception as e:
        print("Email error:", e)
        return False


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
    # If POST from the notify form (legacy), handle it here
    if request.method == "POST" and request.form.get("notify_only"):
        name = request.form.get("name", "Anonymous")
        email = request.form.get("email", "")
        amount = request.form.get("amount", "")
        message = request.form.get("message", "")

        full_message = f"Donation amount: {amount}\n\n{message}"

        if send_email(name, email, full_message):
            flash("✅ Thank you! Donation details sent. We'll reach out to confirm receipt.")
        else:
            flash("❌ Error sending donation info. Please contact us by phone or WhatsApp.")
        return redirect("/donate")

    return render_template("donate.html")


# -------------------------
# Mobile money scaffold
# -------------------------

@app.route("/momo/initiate", methods=["POST"])
def momo_initiate():
    """Initiate a Mobile Money collection request.
    This is a scaffold. You must provide provider credentials and endpoints via env vars.

    Request JSON: { provider: "mtn"|"airtel", phone: "+2567XXXXXXXX", amount: "50000", currency: "UGX" }
    Response JSON: { success: true, tx_ref: "...", message: "..." }
    """
    data = request.json or {}
    provider = data.get("provider")
    phone = data.get("phone")
    amount = data.get("amount")
    currency = data.get("currency", "UGX")

    if provider not in ("mtn", "airtel"):
        return jsonify({"success": False, "message": "Unsupported provider"}), 400
    if not phone or not amount:
        return jsonify({"success": False, "message": "phone and amount are required"}), 400

    tx_ref = str(uuid.uuid4())
    rec = {
        "id": str(uuid.uuid4()),
        "provider": provider,
        "tx_ref": tx_ref,
        "phone": phone,
        "amount": amount,
        "currency": currency,
        "status": "initiated",
        "message": "Initiated by server",
        "created_at": datetime.utcnow().isoformat(),
    }
    save_donation_record(rec)

    # Provider-specific initiation
    try:
        if provider == "mtn":
            # MTN Collection APIs require an access token and specific headers. This is a scaffold.
            # Expected env vars: MTN_API_URL, MTN_API_KEY, MTN_API_SECRET
            mtn_url = os.environ.get("MTN_API_URL")
            if not mtn_url:
                raise RuntimeError("MTN_API_URL not configured")
            # TODO: Obtain access token (depends on MTN environment) and call request-to-pay endpoint.
            # For now return tx_ref and instruct operator to complete the collection via the provider dashboard.
            message = "Initiated. Complete the collection in your MTN MoMo dashboard or use the provider API."
        else:
            # AIRTEL
            airtel_url = os.environ.get("AIRTEL_API_URL")
            if not airtel_url:
                raise RuntimeError("AIRTEL_API_URL not configured")
            # TODO: Implement Airtel collection API call here (token exchange + initiate collection)
            message = "Initiated. Complete the collection in your Airtel Money dashboard or use the provider API."

        # Update record message
        rec["message"] = message
        save_donation_record(rec)

        return jsonify({"success": True, "tx_ref": tx_ref, "message": message})
    except Exception as e:
        rec["status"] = "error"
        rec["message"] = str(e)
        save_donation_record(rec)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/momo/verify", methods=["POST"])
def momo_verify():
    """Verify transaction status by tx_ref. This is provider-specific and must be implemented.
    Request JSON: { provider: "mtn"|"airtel", tx_ref: "..." }
    """
    data = request.json or {}
    provider = data.get("provider")
    tx_ref = data.get("tx_ref")

    if not provider or not tx_ref:
        return jsonify({"success": False, "message": "provider and tx_ref required"}), 400

    # Look up local record
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, provider, tx_ref, phone, amount, currency, status, message, created_at FROM donations WHERE tx_ref = ?", (tx_ref,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"success": False, "message": "tx_ref not found"}), 404

    local_status = row[6]

    # TODO: Call provider verify API to update status. For now return local status.
    return jsonify({
        "success": True,
        "tx_ref": tx_ref,
        "status": local_status,
        "local_record": {
            "id": row[0],
            "provider": row[1],
            "phone": row[3],
            "amount": row[4],
            "currency": row[5],
            "message": row[7],
            "created_at": row[8],
        }
    })


@app.route("/momo/webhook", methods=["POST"])
def momo_webhook():
    """Webhook endpoint for providers to POST payment updates.
    The exact payload depends on provider; we accept JSON and try to extract tx_ref/status.
    Saves the record and sends an email notification.
    """
    payload = request.json or {}
    # Attempt to extract common fields — providers vary in structure
    tx_ref = payload.get("tx_ref") or payload.get("reference") or payload.get("externalId")
    provider = payload.get("provider", "unknown")
    status = payload.get("status") or payload.get("transactionStatus") or "unknown"
    phone = payload.get("phoneNumber") or payload.get("source") or ""
    amount = payload.get("amount") or payload.get("paymentAmount") or ""

    rec = {
        "id": str(uuid.uuid4()),
        "provider": provider,
        "tx_ref": tx_ref or str(uuid.uuid4()),
        "phone": phone,
        "amount": amount,
        "currency": payload.get("currency", "UGX"),
        "status": status,
        "message": json.dumps(payload),
        "created_at": datetime.utcnow().isoformat(),
    }

    save_donation_record(rec)

    # Send an email notification to the site owner
    subject_name = f"Donation notification ({provider})"
    donor_email = payload.get("payerEmail", "")
    email_message = f"Provider: {provider}\nTxRef: {rec['tx_ref']}\nStatus: {status}\nPhone: {phone}\nAmount: {amount}\n\nFull payload:\n{json.dumps(payload, indent=2)}"
    send_email(subject_name, donor_email, email_message)

    # Respond 200 for webhook
    return jsonify({"success": True}), 200


if __name__ == "__main__":
    # Bind to the port provided by the environment (Render, Heroku, etc.)
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
