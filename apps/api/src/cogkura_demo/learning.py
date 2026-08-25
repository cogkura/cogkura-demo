"""Learning feedback construction."""

from __future__ import annotations

from datetime import datetime

from cogkura import LearningFeedback, LearningOutcome, LearningResult, MemoryContext, MemoryFeedback
from cogkura.models import MemoryIdentity

from cogkura_demo.config import CUSTOMER_ID, TENANT_ID
from cogkura_demo.models import LearningChangeResponse


def build_learning_feedback(
    context: MemoryContext,
    *,
    feedback_id: str,
    outcome: LearningOutcome,
    occurred_at: datetime,
) -> LearningFeedback:
    items = tuple(
        MemoryFeedback(
            identity=MemoryIdentity(
                memory_kind=result.memory_kind,
                memory_key=result.memory.memory_key,
            ),
            outcome=outcome,
        )
        for result in context.recall_results
    )
    if not items:
        msg = "Cannot apply learning without selected recall results"
        raise ValueError(msg)
    return LearningFeedback(
        tenant_id=TENANT_ID,
        subject_id=CUSTOMER_ID,
        feedback_id=feedback_id,
        items=items,
        occurred_at=occurred_at,
        goal=context.goal,
    )


def map_learning_result(
    result: LearningResult,
    *,
    outcome: LearningOutcome,
) -> LearningChangeResponse:
    return LearningChangeResponse(
        outcome=outcome.value,
        helpful=result.helpful,
        unhelpful=result.unhelpful,
        incorrect=result.incorrect,
        memories_reinforced=result.memories_reinforced,
        associations_reinforced=result.associations_reinforced,
        association_items_skipped=result.association_items_skipped,
        reactivated=result.reactivated,
    )
