from app.core.models import PlanStep
from app.core.policy_engine import requires_human_approval


def test_policy_flags_destructive_action():
    step = PlanStep(step_id='1', description='Delete all customer records', risk='low')
    assert requires_human_approval(step) is True


def test_policy_allows_low_risk_action():
    step = PlanStep(step_id='1', description='Schedule a team sync', risk='low')
    assert requires_human_approval(step) is False
