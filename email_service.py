from dotenv import load_dotenv
import smtplib
import os

load_dotenv()


def get_email_service():
    email = smtplib.SMTP(os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT'))
    email.starttls()
    email.login(os.getenv('EMAIL'), os.getenv('EMAIL_PASSWORD'))
    return email
