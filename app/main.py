import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from twilio.request_validator import RequestValidator

from .ai import answer_question
from .sms import build_twiml_response, parse_inbound

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CoverageCheck")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# ---------------------------------------------------------------------------
# Rate limiting (in-memory, resets on restart — fine for a demo)
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX = 20       # max requests
RATE_LIMIT_WINDOW = 3600  # per hour (seconds)

_rate_store: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(phone: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_store[phone] if t > window_start]
    _rate_store[phone] = timestamps
    if len(timestamps) >= RATE_LIMIT_MAX:
        return True
    _rate_store[phone].append(now)
    return False


# ---------------------------------------------------------------------------
# Twilio signature validation
# ---------------------------------------------------------------------------
def _validate_twilio_signature(request: Request, form_data: dict) -> bool:
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        logger.warning("TWILIO_AUTH_TOKEN not set — skipping signature validation")
        return True

    validator = RequestValidator(auth_token)
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    return validator.validate(url, form_data, signature)


# ---------------------------------------------------------------------------
# Web chat endpoint
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


@app.get("/")
def index():
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/chat")
async def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        return {"response": "Ask me anything about your plan — like 'what's my urgent care copay?'"}
    logger.info("Web chat question: %r", message)
    answer = answer_question(message)
    logger.info("Web chat response: %r", answer)
    return {"response": answer}


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------
@app.post("/sms")
async def sms_webhook(request: Request):
    form_data = dict(await request.form())

    # Validate Twilio signature in production
    if os.environ.get("VALIDATE_TWILIO_SIGNATURE", "true").lower() == "true":
        if not _validate_twilio_signature(request, form_data):
            logger.warning("Invalid Twilio signature — rejecting request")
            raise HTTPException(status_code=403, detail="Forbidden")

    body, from_number = parse_inbound(form_data)

    # Log question without PII (no phone number)
    logger.info("Incoming question: %r", body)

    # Handle empty messages
    if not body:
        reply = "Text me a question about your plan — like 'what's my urgent care copay?'"
        return Response(content=build_twiml_response(reply), media_type="text/xml")

    # Rate limiting
    if _is_rate_limited(from_number):
        logger.warning("Rate limit hit (number hash=%s)", hash(from_number))
        reply = "You've sent a lot of questions recently. Try again in an hour."
        return Response(content=build_twiml_response(reply), media_type="text/xml")

    # Get answer from Claude
    answer = answer_question(body)
    logger.info("Outgoing response: %r", answer)

    return Response(content=build_twiml_response(answer), media_type="text/xml")


@app.get("/health")
def health():
    return {"status": "ok"}
