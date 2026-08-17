from __future__ import annotations

from reading_evidence.models import QueryPlan
from reading_evidence.text import topic_tokens


def decompose_query(question: str) -> QueryPlan:
    """Create transparent deterministic support/counter retrieval variants."""
    core_tokens = topic_tokens(question)
    if not core_tokens:
        raise ValueError("Question must contain at least one meaningful token")
    core = " ".join(core_tokens)
    return QueryPlan(
        original=question.strip(),
        core=core,
        support=f"{core} reason evidence benefit supports true",
        counter=f"{core} counterexample risk limit exception false",
    )
