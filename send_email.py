import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()

email = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")

def send_email(html_content):

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = "Reddit Product Ideas"
    msg['From'] = email
    msg['To'] = email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(email, password)
        server.send_message(msg)