from reading_evidence.models import EvidenceItem, Relation


DIRECTIONAL_CONFIDENCE_THRESHOLD = 0.6


def abstention_decision(evidence: list[EvidenceItem]) -> tuple[bool, str | None]:
    directional = [
        item
        for item in evidence
        if item.relation in {Relation.SUPPORT, Relation.COUNTER_EVIDENCE}
        and item.confidence >= DIRECTIONAL_CONFIDENCE_THRESHOLD
    ]
    if directional:
        return False, None
    return True, "No sufficiently confident supporting or counter-evidence was retrieved"
