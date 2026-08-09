from flask import Flask, render_template, request
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# ===== EMAIL CONFIG - GMAIL =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'zakmolan@gmail.com'  
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # From Render Environment
app.config['MAIL_DEFAULT_SENDER'] = 'zakmolan@gmail.com'

mail = Mail(app)

# ===== ROUTES =====
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        try:
            msg = Message(
                subject=f"New Website Message from {name}",
                recipients=['zakmolan@gmail.com'],
                body=f"""
New Contact Form Submission - Zakmolanitech

Name: {name}
Email: {email}

Message:
{message}
                """
            )
            mail.send(msg)
            return render_template('contact.html', success=True)
        
        except Exception as e:
            print(f"Email Error: {e}")
            return render_template('contact.html', error=True)
    
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
