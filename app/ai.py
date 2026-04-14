import logging
import os
from typing import Optional

import anthropic

from .benefits import get_plan_summary
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def answer_question(member_message: str) -> str:
    """
    Send the member's question + plan data to Claude and return the answer.
    Falls back to a friendly error message if the API call fails.
    """
    plan_data = get_plan_summary()
    user_content = f"Member question: {member_message}\n\nPlan data:\n{plan_data}"

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        answer = response.content[0].text.strip()
        logger.info("AI response generated (length=%d)", len(answer))
        return answer
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API error: status=%d message=%s", e.status_code, e.message)
        return "Sorry, I'm having trouble right now. Try again in a minute."
    except anthropic.APIConnectionError:
        logger.error("Anthropic API connection error")
        return "Sorry, I'm having trouble right now. Try again in a minute."
    except Exception:
        logger.exception("Unexpected error calling Claude API")
        return "Sorry, I'm having trouble right now. Try again in a minute."
