from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "zakmolanitech_secret_2026"  # needed for flash messages

# EMAIL CONFIG - Replace with your gmail app password
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yourgmail@gmail.com'  # CHANGE THIS
app.config['MAIL_PASSWORD'] = 'your_app_password'    # CHANGE THIS
app.config['MAIL_DEFAULT_SENDER'] = 'yourgmail@gmail.com'

mail = Mail(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/portfolio')  # <-- FIXED: No indentation
def portfolio():
    return render_template('portfolio.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        try:
            msg = Message(
                subject=f"New Contact from {name}",
                recipients=['yourgmail@gmail.com'], # Emails will come here
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            )
            mail.send(msg)
            flash('Message sent successfully!', 'success')
        except Exception as e:
            flash('Error sending message. Please try again.', 'error')
            print(e)
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

if __name__ == '__main__':
    import requests
from flask import request, jsonify

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

@app.route('/send-contact', methods=['POST'])
def send_contact():
    data = request.get_json()
    text = f"🚨 NEW LEAD - Zakmolanitech\nName: {data['name']}\nEmail: {data['email']}\nMessage: {data['message']}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    return jsonify({"status": "ok"})
    app.run(debug=True)
