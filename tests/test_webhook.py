"""Tests for the Twilio webhook endpoint."""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# Disable signature validation for tests
os.environ["VALIDATE_TWILIO_SIGNATURE"] = "false"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["TWILIO_AUTH_TOKEN"] = "test-token"


from app.main import app, _rate_store

client = TestClient(app)


def _twilio_post(body: str, from_number: str = "+15550001234"):
    return client.post(
        "/sms",
        data={"Body": body, "From": from_number},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


@patch("app.main.answer_question", return_value="Your urgent care copay is $75.")
def test_sms_endpoint_returns_200(mock_ai):
    response = _twilio_post("what's my copay for urgent care?")
    assert response.status_code == 200


@patch("app.main.answer_question", return_value="Your urgent care copay is $75.")
def test_sms_endpoint_returns_xml(mock_ai):
    response = _twilio_post("what's my copay for urgent care?")
    assert "text/xml" in response.headers["content-type"]


@patch("app.main.answer_question", return_value="Your urgent care copay is $75.")
def test_sms_response_contains_twiml_response_tag(mock_ai):
    response = _twilio_post("what's my copay for urgent care?")
    assert "<Response>" in response.text


@patch("app.main.answer_question", return_value="Your urgent care copay is $75.")
def test_sms_response_contains_message_tag(mock_ai):
    response = _twilio_post("what's my copay for urgent care?")
    assert "<Message>" in response.text


@patch("app.main.answer_question", return_value="Your urgent care copay is $75.")
def test_sms_response_contains_answer_text(mock_ai):
    response = _twilio_post("what's my copay for urgent care?")
    assert "Your urgent care copay is $75." in response.text


@patch("app.main.answer_question", return_value="Copay is $30.")
def test_empty_body_returns_prompt(mock_ai):
    response = _twilio_post("")
    assert response.status_code == 200
    assert "question" in response.text.lower() or "text" in response.text.lower()
    mock_ai.assert_not_called()


@patch("app.main.answer_question", return_value="Copay is $30.")
def test_whitespace_only_body_returns_prompt(mock_ai):
    response = _twilio_post("   ")
    assert response.status_code == 200
    mock_ai.assert_not_called()


@patch("app.main.answer_question", return_value="Copay is $30.")
def test_rate_limit_blocks_after_max_requests(mock_ai):
    _rate_store.clear()
    number = "+15559998888"
    # Hit the limit
    for _ in range(20):
        r = _twilio_post("copay?", from_number=number)
        assert r.status_code == 200

    # 21st request should be rate-limited
    response = _twilio_post("copay?", from_number=number)
    assert response.status_code == 200
    assert "hour" in response.text.lower() or "limit" in response.text.lower() or "try again" in response.text.lower()
    _rate_store.clear()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.answer_question", return_value="A" * 500)
def test_very_long_ai_response_is_truncated(mock_ai):
    response = _twilio_post("what's everything about my plan?")
    assert response.status_code == 200
    # The TwiML message content should not exceed 403 chars (400 + "...")
    import re
    match = re.search(r"<Message>(.*?)</Message>", response.text, re.DOTALL)
    assert match is not None
    assert len(match.group(1)) <= 403
