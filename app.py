from flask import Flask, render_template, request, redirect, flash
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
# Read secret key from environment, with a safe default for local testing
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "zakmolan_secret_2026")

# Email configuration — set these as environment variables in production
YOUR_EMAIL = os.environ.get("EMAIL_ADDRESS", "zakmolan@gmail.com")
YOUR_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Must be set in the environment


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


if __name__ == "__main__":
    # Bind to the port provided by the environment (Render, Heroku, etc.)
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
