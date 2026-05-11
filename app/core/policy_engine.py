from app.core.models import PlanStep

DESTRUCTIVE_VERBS = {"delete", "drop", "remove", "destroy", "truncate"}


def requires_human_approval(step: PlanStep) -> bool:
    text = step.description.lower()
    return step.risk in {"high", "restricted"} or any(v in text for v in DESTRUCTIVE_VERBS)


def approval_context(step: PlanStep) -> dict[str, str]:
    return {
        "step_id": step.step_id,
        "action_summary": step.description,
        "risk": step.risk,
        "reversibility": "unknown",
    }
