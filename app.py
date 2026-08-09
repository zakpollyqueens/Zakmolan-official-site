from flask import Flask, render_template, request
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# EMAIL CONFIG - GMAIL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'zakmolan@gmail.com'  # YOUR EMAIL
app.config['MAIL_PASSWORD'] = 'your-app-password'   # GMAIL APP PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = 'zakmolan@gmail.com'

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

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Send email to you
        msg = Message(
            subject=f"New Website Message from {name}",
            recipients=['zakmolan@gmail.com'],  # emails come here
            body=f"""
New Contact Form Submission

Name: {name}
Email: {email}

Message:
{message}
            """
        )
        mail.send(msg)
        
        return render_template('contact.html', success=True)
    
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
