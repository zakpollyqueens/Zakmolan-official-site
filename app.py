from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
import os
import requests
from dotenv import load_dotenv

load_dotenv() # for local testing

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'zakmolanitech-secret-key')

# ====== CONFIG ======
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ====== ROUTES ======
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html',
        paypal_env = os.getenv('PAYPAL_ENV', 'production'),
        paypal_main = os.getenv('PAYPAL_BUTTON_ID_MAIN'),
        paypal_10 = os.getenv('PAYPAL_BUTTON_ID_10'),
        paypal_25 = os.getenv('PAYPAL_BUTTON_ID_25'),
        paypal_50 = os.getenv('PAYPAL_BUTTON_ID_50')
    )

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/donate')
def donate():
    return render_template('donate.html')

# ====== CONTACT FORM HANDLER ======
@app.route('/send-contact', methods=['POST'])
def send_contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    errors = []
    success_count = 0
    
    # 1. SEND EMAIL
    try:
        if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            msg = Message(
                subject=f'🚨 New Lead from {name} - Zakmolanitech',
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_USERNAME']]
            )
            msg.body = f"""
            You got a new message from the website:
            
            Name: {name}
            Email: {email}
            Message: {message}
            """
            mail.send(msg)
            success_count += 1
        else:
            errors.append("Email Error: MAIL_USERNAME or MAIL_PASSWORD missing")
    except Exception as e:
        errors.append(f"Email Error: {str(e)}")
        print("EMAIL ERROR:", e)

    # 2. SEND TELEGRAM
    try:
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            text = f"""🚨 NEW LEAD - Zakmolanitech
            
Name: {name}
Email: {email}
Message: {message}"""
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                success_count += 1
            else:
                errors.append(f"Telegram Error: {r.text}")
        else:
            errors.append("Telegram Error: BOT_TOKEN or CHAT_ID missing")
    except Exception as e:
        errors.append(f"Telegram Error: {str(e)}")
        print("TELEGRAM ERROR:", e)

    # 3. RETURN RESPONSE
    if success_count > 0:
        return jsonify({"status": "success", "message": "Message sent!"}), 200
    else:
        return jsonify({"status": "error", "errors": errors}), 500

if __name__ == '__main__':
    app.run(debug=True)
