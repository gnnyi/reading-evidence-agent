from reading_evidence.models import EvidenceItem, Relation


def abstention_decision(evidence: list[EvidenceItem]) -> tuple[bool, str | None]:
    directional = [
        item
        for item in evidence
        if item.relation in {Relation.SUPPORT, Relation.COUNTER_EVIDENCE}
        and item.confidence >= 0.6
    ]
    if directional:
        return False, None
    return True, "No sufficiently confident supporting or counter-evidence was retrieved"
