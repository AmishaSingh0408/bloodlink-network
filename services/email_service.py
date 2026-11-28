
import os
import smtplib
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

# Load credentials from the project's .env file
load_dotenv()

logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT")


def send_email(subject: str, body: str) -> bool:
    """
    Send an email using Gmail SMTP.

    Returns True if successful, False otherwise.
    """

    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or not ALERT_RECIPIENT:
        logger.warning("Email settings are missing. Notification skipped.")
        return False

    message = EmailMessage()
    message["From"] = SMTP_EMAIL
    message["To"] = ALERT_RECIPIENT
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(message)

        logger.info("Email notification sent successfully.")
        return True

    except Exception:
        logger.exception("Email notification could not be sent.")
        return False


def send_transfer_notification(
    request_id: str,
    shortage_hospital: str,
    supplier_hospital: str,
    blood_type: str,
    units: int,
    status: str = "PENDING",
) -> bool:

    subject = f"BloodLink: Transfer Request {status}"

    body = f"""
BloodLink Network - Transfer Notification

Request ID: {request_id}

Shortage Hospital: {shortage_hospital}
Supplier Hospital: {supplier_hospital}
Blood Type: {blood_type}
Recommended Units: {units}

Current Status: {status}

This is a simulated coordination notification.
No actual blood transfer has been initiated.
"""

    return send_email(subject, body)
