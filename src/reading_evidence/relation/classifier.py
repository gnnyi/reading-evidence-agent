from __future__ import annotations

from reading_evidence.models import Relation, RetrievalCandidate
from reading_evidence.text import PREDICATE_HINTS, claim_has_negative_polarity, topic_tokens


def classify_candidate(question: str, candidate: RetrievalCandidate) -> tuple[Relation, float, str]:
    """A deterministic public baseline, not a claim of semantic entailment."""
    ordered_question_tokens = topic_tokens(question)
    question_tokens = set(ordered_question_tokens)
    note_tokens = set(topic_tokens(f"{candidate.note.title} {candidate.note.text}"))
    overlap = question_tokens & note_tokens
    overlap_ratio = len(overlap) / max(len(question_tokens), 1)

    if len(overlap) < 2 or overlap_ratio < 0.25:
        topical_overlap = overlap - PREDICATE_HINTS
        if topical_overlap:
            return Relation.RELATED, min(0.49, 0.25 + overlap_ratio), "Shares a topic but not enough of the claim"
        return Relation.IRRELEVANT, 0.1, "No meaningful claim-level token overlap"

    anchors = (question_tokens & PREDICATE_HINTS) or set(ordered_question_tokens[-2:])
    question_negative = claim_has_negative_polarity(question, anchors)
    note_negative = claim_has_negative_polarity(
        f"{candidate.note.title} {candidate.note.text}", anchors
    )
    opposite_polarity = question_negative != note_negative
    confidence = min(0.95, 0.45 + overlap_ratio * 0.5)
    if opposite_polarity:
        return Relation.COUNTER_EVIDENCE, confidence, "Overlapping claim with opposite explicit polarity"
    if overlap_ratio >= 0.5:
        return Relation.SUPPORT, confidence, "Overlapping claim with matching explicit polarity"
    topical_overlap = overlap - PREDICATE_HINTS
    if len(topical_overlap) >= 2:
        return Relation.RELATED, min(0.74, confidence), "Contextual overlap without a strong directional relation"
    return Relation.IRRELEVANT, 0.2, "Overlap is limited to a broad topic and generic predicate"
