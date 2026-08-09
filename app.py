from flask import Flask, render_template, request, redirect, flash
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "zakmolan_secret_2026"

# Your email details
YOUR_EMAIL = "zakmolan@gmail.com"
YOUR_PASSWORD = "your_app_password" # Get Gmail App Password

def send_email(name, email, message):
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
            flash("✅ Message sent! We'll reply to you soon at zakmolan@gmail.com")
        else:
            flash("❌ Error sending message. Please call 256 742956448")
        return redirect("/contact")
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)
