from flask import Flask, render_template, request, redirect, flash, jsonify
import smtplib
from email.mime.text import MIMEText
import os
import requests
import sqlite3
import uuid
import json
from datetime import datetime
import hmac
import hashlib
import base64

app = Flask(__name__)
# Read secret key from environment, with a safe default for local testing
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "zakmolan_secret_2026")

# Email configuration — set these as environment variables in production
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS", "zakmolan@gmail.com")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Must be set in the environment

# Environment mode for providers: sandbox or production
MTN_ENV = os.environ.get("MTN_ENV", "sandbox")
AIRTEL_ENV = os.environ.get("AIRTEL_ENV", "sandbox")
FLW_ENV = os.environ.get("FLW_ENV", "live")

# Mobile money config env var names (placeholders — set in your host)
# MTN: MTN_API_URL, MTN_TOKEN_URL, MTN_CLIENT_ID, MTN_CLIENT_SECRET, MTN_SUBSCRIPTION_KEY, MTN_WEBHOOK_SECRET
# AIRTEL: AIRTEL_API_URL, AIRTEL_TOKEN_URL, AIRTEL_CLIENT_ID, AIRTEL_CLIENT_SECRET, AIRTEL_SUBSCRIPTION_KEY, AIRTEL_WEBHOOK_SECRET
# Flutterwave: FLW_SECRET_KEY, FLW_PUBLIC_KEY, FLW_WEBHOOK_SECRET, FLW_ENV (live|sandbox)

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
# MTN & Airtel placeholders (kept as before)
# -------------------------
# (existing MTN/Airtel functions omitted for brevity in this file excerpt — they remain unchanged)


def get_mtn_token():
    token_url = os.environ.get("MTN_TOKEN_URL")
    client_id = os.environ.get("MTN_CLIENT_ID")
    client_secret = os.environ.get("MTN_CLIENT_SECRET")
    if not token_url or not client_id or not client_secret:
        print("MTN token config missing: MTN_TOKEN_URL/MTN_CLIENT_ID/MTN_CLIENT_SECRET")
        return None
    try:
        auth = (client_id, client_secret)
        r = requests.post(token_url, data={"grant_type": "client_credentials"}, auth=auth, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("access_token") or data.get("token")
    except Exception as e:
        print("MTN token exchange failed:", e)
        return None


def initiate_mtn_collection(phone, amount, currency, tx_ref):
    mtn_url = os.environ.get("MTN_API_URL")
    if not mtn_url:
        raise RuntimeError("MTN_API_URL not configured")
    access_token = get_mtn_token()
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    subscription = os.environ.get("MTN_SUBSCRIPTION_KEY")
    if subscription:
        headers["Ocp-Apim-Subscription-Key"] = subscription
    payload = {
        "amount": str(amount),
        "currency": currency,
        "externalId": tx_ref,
        "payer": {"partyIdType": "MSISDN", "partyId": phone},
        "payerMessage": f"Donation {tx_ref}",
        "payeeNote": "Zakmolanitechsolutions donation"
    }
    endpoint = mtn_url.rstrip('/') + '/collection/v1_0/requesttopay'
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201, 202):
            location = r.headers.get('Location') or ''
            return {"success": True, "message": f"Request-to-pay initiated (status {r.status_code}).", "location": location}
        return {"success": False, "message": f"Provider responded: {r.status_code} {r.text}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def verify_mtn_tx(tx_ref):
    mtn_url = os.environ.get("MTN_API_URL")
    if not mtn_url:
        raise RuntimeError("MTN_API_URL not configured")
    access_token = get_mtn_token()
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    subscription = os.environ.get("MTN_SUBSCRIPTION_KEY")
    if subscription:
        headers["Ocp-Apim-Subscription-Key"] = subscription
    endpoint = mtn_url.rstrip('/') + f'/collection/v1_0/requesttopay/{tx_ref}'
    try:
        r = requests.get(endpoint, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "message": f"Provider responded: {r.status_code} {r.text}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_airtel_token():
    token_url = os.environ.get("AIRTEL_TOKEN_URL")
    client_id = os.environ.get("AIRTEL_CLIENT_ID")
    client_secret = os.environ.get("AIRTEL_CLIENT_SECRET")
    if not token_url or not client_id or not client_secret:
        print("Airtel token config missing")
        return None
    try:
        auth = (client_id, client_secret)
        r = requests.post(token_url, data={"grant_type": "client_credentials"}, auth=auth, timeout=10)
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception as e:
        print("Airtel token error:", e)
        return None


def initiate_airtel_collection(phone, amount, currency, tx_ref):
    airtel_url = os.environ.get("AIRTEL_API_URL")
    if not airtel_url:
        raise RuntimeError("AIRTEL_API_URL not configured")
    access_token = get_airtel_token()
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    subscription = os.environ.get("AIRTEL_SUBSCRIPTION_KEY")
    if subscription:
        headers["Ocp-Apim-Subscription-Key"] = subscription
    payload = {
        "amount": str(amount),
        "currency": currency,
        "externalId": tx_ref,
        "payer": {"partyIdType": "MSISDN", "partyId": phone},
        "payerMessage": f"Donation {tx_ref}",
        "payeeNote": "Zakmolanitechsolutions donation"
    }
    endpoint = airtel_url.rstrip('/') + '/collection/v1_0/requesttopay'
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201, 202):
            return {"success": True, "message": f"Request-to-pay initiated (status {r.status_code})."}
        return {"success": False, "message": f"Provider responded: {r.status_code} {r.text}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# -------------------------
# Flutterwave implementation
# -------------------------

FLW_API_BASE = os.environ.get("FLW_API_BASE", "https://api.flutterwave.com/v3")
FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.environ.get("FLW_PUBLIC_KEY")
FLW_WEBHOOK_SECRET = os.environ.get("FLW_WEBHOOK_SECRET")


def create_flw_payment_link(amount, currency, tx_ref, redirect_url, customer):
    """Create a Flutterwave payment. Returns dict with success and link/message."""
    if not FLW_SECRET_KEY:
        return {"success": False, "message": "FLW_SECRET_KEY not configured"}

    endpoint = FLW_API_BASE.rstrip('/') + '/payments'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {FLW_SECRET_KEY}'
    }
    payload = {
        "tx_ref": tx_ref,
        "amount": str(amount),
        "currency": currency,
        "redirect_url": redirect_url,
        "customer": customer,
        "meta": {"reason": "Zakmolanitechsolutions donation"}
    }
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        # data['data']['link'] usually contains the hosted payment page
        link = data.get('data', {}).get('link')
        return {"success": True, "link": link, "raw": data}
    except Exception as e:
        return {"success": False, "message": str(e)}


def verify_flw_payment(tx_ref):
    if not FLW_SECRET_KEY:
        return {"success": False, "message": "FLW_SECRET_KEY not configured"}
    endpoint = FLW_API_BASE.rstrip('/') + f'/transactions/verify_by_reference?reference={tx_ref}'
    headers = {'Authorization': f'Bearer {FLW_SECRET_KEY}'}
    try:
        r = requests.get(endpoint, headers=headers, timeout=10)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except Exception as e:
        return {"success": False, "message": str(e)}


# -------------------------
# Routes (existing + new payments endpoints)
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


@app.route("/payments/create", methods=["POST"])
def payments_create():
    """Create a Flutterwave payment session and return the hosted payment link."""
    data = request.json or {}
    amount = data.get('amount')
    currency = data.get('currency', 'UGX')
    donor_email = data.get('donor_email', '')
    phone = data.get('phone', '')
    name = data.get('name', '')

    if not amount:
        return jsonify({'success': False, 'message': 'amount required'}), 400

    tx_ref = f"flw_{uuid.uuid4()}"
    redirect_url = data.get('redirect_url') or (request.url_root.rstrip('/') + '/payments/return')
    customer = {"email": donor_email or "", "phonenumber": phone or "", "name": name or "Donor"}

    # Save local donation record with provider flutterwave
    rec = {
        'id': str(uuid.uuid4()),
        'provider': 'flutterwave',
        'tx_ref': tx_ref,
        'phone': phone,
        'amount': amount,
        'currency': currency,
        'status': 'initiated',
        'message': 'Waiting for user to complete payment on Flutterwave',
        'donor_email': donor_email,
        'created_at': datetime.utcnow().isoformat()
    }
    save_donation_record(rec)

    flw = create_flw_payment_link(amount, currency, tx_ref, redirect_url, customer)
    if not flw.get('success'):
        rec['status'] = 'error'
        rec['message'] = flw.get('message')
        save_donation_record(rec)
        return jsonify({'success': False, 'message': flw.get('message')}), 500

    # Update record with message
    rec['message'] = 'Payment link created'
    rec['status'] = 'pending'
    save_donation_record(rec)

    return jsonify({'success': True, 'link': flw.get('link'), 'tx_ref': tx_ref})


@app.route('/payments/return')
def payments_return():
    # This is the redirect URL Flutterwave returns donors to after payment.
    # We simply show a thank-you page and leave verification to webhooks.
    return render_template('payments_return.html')


@app.route('/payments/verify', methods=['POST'])
def payments_verify():
    data = request.json or {}
    tx_ref = data.get('tx_ref')
    if not tx_ref:
        return jsonify({'success': False, 'message': 'tx_ref required'}), 400

    local = get_donation_by_tx(tx_ref)
    if not local:
        return jsonify({'success': False, 'message': 'tx_ref not found'}), 404

    prov = verify_flw_payment(tx_ref)
    if not prov.get('success'):
        return jsonify({'success': False, 'message': prov.get('message')}), 502

    # Provider response structure varies; save the whole response
    update_donation_status(tx_ref, 'verified', json.dumps(prov.get('data')))
    local = get_donation_by_tx(tx_ref)
    return jsonify({'success': True, 'tx_ref': tx_ref, 'local_record': local})


@app.route('/payments/webhook', methods=['POST'])
def payments_webhook():
    # Flutterwave sends a 'verif-hash' header computed with your webhook secret
    body = request.get_data() or b''
    sig_header = request.headers.get('verif-hash') or request.headers.get('VERIF-HASH')
    secret = FLW_WEBHOOK_SECRET

    # If secret is set, verify
    if secret and sig_header:
        computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, sig_header):
            print('Flutterwave webhook signature mismatch')
            return jsonify({'success': False, 'message': 'signature mismatch'}), 403

    payload = request.json or {}
    event = payload.get('event') or payload.get('data', {}).get('status') or payload.get('data', {}).get('tx_ref')
    data = payload.get('data') or payload

    # Extract reference and status (common fields)
    tx_ref = data.get('tx_ref') or data.get('reference') or data.get('id')
    status = data.get('status') or data.get('transaction_status') or 'unknown'
    amount = data.get('amount') or data.get('charged_amount') or ''
    currency = data.get('currency') or ''
    customer = data.get('customer') or {}
    donor_email = customer.get('email') or data.get('customer_email') or ''

    if tx_ref:
        loc = get_donation_by_tx(tx_ref)
        if loc:
            update_donation_status(tx_ref, status, json.dumps(payload))
        else:
            rec = {
                'id': str(uuid.uuid4()),
                'provider': 'flutterwave',
                'tx_ref': tx_ref,
                'phone': customer.get('phonenumber') if isinstance(customer, dict) else '',
                'amount': amount,
                'currency': currency,
                'status': status,
                'message': json.dumps(payload),
                'donor_email': donor_email,
                'created_at': datetime.utcnow().isoformat()
            }
            save_donation_record(rec)

    # Send receipt/notification on successful charge
    success_states = {'successful', 'success', 'completed', 'paid', 'PAID'}
    if str(status).lower() in success_states:
        # Notify owner and donor
        local = get_donation_by_tx(tx_ref) or {}
        donor = donor_email or local.get('donor_email') if local else None
        owner_msg = f"Payment received via Flutterwave\nTxRef: {tx_ref}\nStatus: {status}\nAmount: {amount} {currency}\n\nFull payload:\n{json.dumps(payload, indent=2)}"
        send_email(f"Donation received: {tx_ref}", donor or YOUR_EMAIL, owner_msg)

    return jsonify({'success': True}), 200


# Keep existing momo endpoints (initiate/verify/webhook) in app.py — they remain available

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
