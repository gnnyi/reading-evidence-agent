from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Relation(str, Enum):
    SUPPORT = "SUPPORT"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    RELATED = "RELATED"
    IRRELEVANT = "IRRELEVANT"


@dataclass(frozen=True)
class RelationJudgment:
    """One judge decision plus optional source-grounding and safe telemetry."""

    relation: Relation
    confidence: float
    reason: str
    evidence_line: int | None = None
    evidence_quote: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Note:
    note_id: str
    title: str
    text: str
    source: str
    line_start: int = 1


@dataclass
class RetrievalCandidate:
    note: Note
    rrf_score: float
    best_lexical_score: float
    matched_queries: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EvidenceItem:
    note_id: str
    title: str
    excerpt: str
    relation: Relation
    confidence: float
    citation: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["relation"] = self.relation.value
        return value


@dataclass(frozen=True)
class QueryPlan:
    original: str
    core: str
    support: str
    counter: str

    def as_list(self) -> list[str]:
        return [self.original, self.support, self.counter]


@dataclass
class Answer:
    question: str
    evidence: list[EvidenceItem]
    abstained: bool
    abstention_reason: str | None
    trace: dict[str, Any]
    status: str = "OK"

    def by_relation(self, relation: Relation) -> list[EvidenceItem]:
        return [item for item in self.evidence if item.relation == relation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "question": self.question,
            "abstained": self.abstained,
            "abstention_reason": self.abstention_reason,
            "evidence": [item.to_dict() for item in self.evidence],
            "trace": self.trace,
        }
