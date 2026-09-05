"""Application evidence policy for semantic promotion.

The Demo decides which observations are strong enough to become semantic
assertions. CogKura still owns activation, forgetting, and working memory.

0.3.13 policy: isolated browse and support interactions remain episodic.
Authored semantic facts on purchase, return, preference, and review events
are passed through unchanged. The policy never invents facts and never
reads gold, query text, or activity names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from cogkura_demo.scenarios import HistoryEvent, SemanticFactSpec

EvidenceClass = Literal["episode_only", "semantic_eligible"]

EPISODE_ONLY_EVENT_TYPES: frozenset[str] = frozenset({"browse", "support_interaction"})
SEMANTIC_ELIGIBLE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "purchase",
        "product_return",
        "preference_statement",
        "positive_outcome",
        "negative_outcome",
    }
)


def evidence_class_for_event(event: HistoryEvent) -> EvidenceClass:
    if event.type in EPISODE_ONLY_EVENT_TYPES:
        return "episode_only"
    if event.type in SEMANTIC_ELIGIBLE_EVENT_TYPES:
        return "semantic_eligible"
    msg = f"Unsupported event type for evidence policy: {event.type}"
    raise ValueError(msg)


def semantic_facts_for_observation(event: HistoryEvent) -> list[SemanticFactSpec]:
    if evidence_class_for_event(event) == "episode_only":
        return []
    return list(event.semantic_facts)
