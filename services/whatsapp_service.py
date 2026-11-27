
import os
import logging

from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_WHATSAPP_RECIPIENT = os.getenv("TWILIO_WHATSAPP_RECIPIENT")


def send_whatsapp_message(body: str) -> bool:
    """Send a WhatsApp message through the Twilio Sandbox."""

    if not all([
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_WHATSAPP_NUMBER,
        TWILIO_WHATSAPP_RECIPIENT,
    ]):
        logger.warning("Twilio settings are missing. WhatsApp notification skipped.")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=TWILIO_WHATSAPP_RECIPIENT,
            body=body,
        )

        logger.info("WhatsApp notification submitted. Message SID: %s", message.sid)
        return True

    except TwilioRestException:
        logger.exception("Twilio could not send the WhatsApp message.")
        return False

    except Exception:
        logger.exception("Unexpected WhatsApp notification error.")
        return False


def send_transfer_whatsapp_notification(
    request_id: str,
    shortage_hospital: str,
    supplier_hospital: str,
    blood_type: str,
    units: int,
    status: str,
) -> bool:
    """Send a simulated transfer status notification."""

    body = f"""
BloodLink Network - Transfer Notification

Request ID: {request_id}
Shortage Hospital: {shortage_hospital}
Supplier Hospital: {supplier_hospital}
Blood Type: {blood_type}
Recommended Units: {units}
Status: {status}

This is a simulated coordination notification.
No actual blood transfer has been initiated.
"""

    return send_whatsapp_message(body.strip())
