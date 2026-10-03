"""Low-level IPPanel delivery without product-specific side effects."""

import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_iranian_phone(phone_number: str) -> str:
    """Return an Iranian mobile number in the E.164 form required by IPPanel."""
    normalized = (phone_number or "").translate(_PERSIAN_DIGITS)
    normalized = re.sub(r"[\s\-()]", "", normalized)
    if normalized.startswith("0098"):
        normalized = "+" + normalized[2:]
    elif normalized.startswith("98"):
        normalized = "+" + normalized
    elif normalized.startswith("09"):
        normalized = "+98" + normalized[1:]
    return normalized


def send_sms(phone_number: str, message: str) -> bool:
    """Send a plain-text webservice SMS through IPPanel.

    This function intentionally has no template/pattern branch. Every caller
    supplies the final text and keeps its own product-specific logging.
    """
    if not settings.IPPANEL_API_TOKEN or not settings.IPPANEL_SENDER:
        logger.warning("SMS skipped because IPPanel credentials are not configured.")
        return False

    recipient = normalize_iranian_phone(phone_number)
    sender = normalize_iranian_phone(settings.IPPANEL_SENDER)
    if not recipient.startswith("+989"):
        logger.warning("SMS skipped because recipient is not a valid Iranian mobile number.")
        return False

    try:
        response = requests.post(
            "https://edge.ippanel.com/v1/api/send",
            headers={"Authorization": settings.IPPANEL_API_TOKEN},
            json={
                "sending_type": "webservice",
                "from_number": sender,
                "message": message,
                "params": {"recipients": [recipient]},
            },
            timeout=15,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        if not response.ok:
            logger.error(
                "IPPanel rejected SMS for %s (HTTP %s): %s",
                recipient,
                response.status_code,
                payload,
            )
            return False

        if payload.get("meta", {}).get("status") is not True:
            logger.error("IPPanel did not accept SMS for %s: %s", recipient, payload)
            return False
        return True
    except requests.RequestException:
        logger.exception("IPPanel delivery failed for %s.", recipient)
        return False
