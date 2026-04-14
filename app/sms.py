import logging
from xml.etree.ElementTree import Element, SubElement, tostring

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 400  # SMS practical limit; Twilio handles splitting but we keep it clean
MAX_INBOUND_LENGTH = 1600  # Ignore absurdly long inputs


def parse_inbound(form_data: dict) -> tuple[str, str]:
    """
    Extract the message body and sender from a Twilio webhook POST.
    Returns (body, from_number). Body is stripped and truncated if needed.
    """
    body = form_data.get("Body", "").strip()
    from_number = form_data.get("From", "unknown")

    if len(body) > MAX_INBOUND_LENGTH:
        body = body[:MAX_INBOUND_LENGTH]

    return body, from_number


def build_twiml_response(message: str) -> str:
    """
    Wrap a text message in TwiML XML so Twilio sends it as an SMS reply.
    Truncates to MAX_MESSAGE_LENGTH if needed.
    """
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[: MAX_MESSAGE_LENGTH - 3] + "..."
        logger.warning("Response truncated to %d chars", MAX_MESSAGE_LENGTH)

    response = Element("Response")
    message_el = SubElement(response, "Message")
    message_el.text = message

    return '<?xml version="1.0" encoding="UTF-8"?>' + tostring(response, encoding="unicode")
