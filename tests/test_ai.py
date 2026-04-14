"""Tests for the AI question-answering module (Claude API mocked)."""
from unittest.mock import MagicMock, patch

import pytest

from app.ai import answer_question


def _mock_response(text: str) -> MagicMock:
    """Build a mock Anthropic messages.create response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


@patch("app.ai._get_client")
def test_urgent_care_copay_question(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "Your urgent care copay is $75."
    )
    result = answer_question("what's my copay for urgent care?")
    assert "$75" in result
    assert "urgent care" in result.lower()


@patch("app.ai._get_client")
def test_therapy_coverage_question(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "Yes, mental health therapy is covered. Your copay is $30 per session."
    )
    result = answer_question("is therapy covered?")
    assert "$30" in result


@patch("app.ai._get_client")
def test_generic_rx_question(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "Amoxicillin is a Tier 1 generic. Your copay is $10."
    )
    result = answer_question("how much does amoxicillin cost?")
    assert "$10" in result


@patch("app.ai._get_client")
def test_gym_not_covered(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "No, gym memberships aren't covered under your plan."
    )
    result = answer_question("is my gym membership covered?")
    assert "not covered" in result.lower() or "aren't covered" in result.lower()


@patch("app.ai._get_client")
def test_referral_question(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "No, your PPO plan doesn't require referrals for specialist visits."
    )
    result = answer_question("do I need a referral for a specialist?")
    assert "referral" in result.lower()
    assert "no" in result.lower()


@patch("app.ai._get_client")
def test_response_is_stripped(mock_get_client):
    mock_get_client.return_value.messages.create.return_value = _mock_response(
        "  Your copay is $25.  "
    )
    result = answer_question("primary care copay?")
    assert result == "Your copay is $25."


@patch("app.ai._get_client")
def test_api_status_error_returns_fallback(mock_get_client):
    import anthropic
    mock_get_client.return_value.messages.create.side_effect = anthropic.APIStatusError(
        message="Service unavailable",
        response=MagicMock(status_code=503, headers={}),
        body=None,
    )
    result = answer_question("what's my deductible?")
    assert "trouble" in result.lower()
    assert "try again" in result.lower()


@patch("app.ai._get_client")
def test_api_connection_error_returns_fallback(mock_get_client):
    import anthropic
    mock_get_client.return_value.messages.create.side_effect = anthropic.APIConnectionError(
        request=MagicMock()
    )
    result = answer_question("what's my deductible?")
    assert "trouble" in result.lower()


@patch("app.ai._get_client")
def test_unexpected_error_returns_fallback(mock_get_client):
    mock_get_client.return_value.messages.create.side_effect = RuntimeError("boom")
    result = answer_question("what's my deductible?")
    assert "trouble" in result.lower()


@patch("app.ai._get_client")
def test_correct_model_used(mock_get_client):
    mock_create = mock_get_client.return_value.messages.create
    mock_create.return_value = _mock_response("Your deductible is $1,500.")
    answer_question("what's my deductible?")
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"


@patch("app.ai._get_client")
def test_max_tokens_is_reasonable(mock_get_client):
    mock_create = mock_get_client.return_value.messages.create
    mock_create.return_value = _mock_response("Your deductible is $1,500.")
    answer_question("what's my deductible?")
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["max_tokens"] <= 300


@patch("app.ai._get_client")
def test_plan_data_included_in_request(mock_get_client):
    mock_create = mock_get_client.return_value.messages.create
    mock_create.return_value = _mock_response("Your deductible is $1,500.")
    answer_question("what's my deductible?")
    call_kwargs = mock_create.call_args
    messages = call_kwargs.kwargs["messages"]
    assert any("plan" in str(m).lower() for m in messages)
