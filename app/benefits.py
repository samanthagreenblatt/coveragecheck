import json
from pathlib import Path

_PLAN_PATH = Path(__file__).parent.parent / "data" / "plan.json"

def load_plan() -> dict:
    """Load the benefit plan data from JSON."""
    with open(_PLAN_PATH) as f:
        return json.load(f)


def get_plan_summary() -> str:
    """Return the plan data as a formatted JSON string for use in prompts."""
    plan = load_plan()
    return json.dumps(plan, indent=2)
