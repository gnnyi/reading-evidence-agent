from __future__ import annotations

import re


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "but", "by",
    "can", "could", "do", "does", "for", "from", "how", "i", "if", "in",
    "into", "is", "it", "my", "of", "on", "or", "should", "that", "the",
    "their", "this", "to", "treat", "was", "what", "when", "whether", "with",
}

CANONICAL = {
    "failed": "fail",
    "failure": "fail",
    "failures": "fail",
    "failing": "fail",
    "experiments": "experiment",
    "experimental": "experiment",
    "wasted": "waste",
    "wasting": "waste",
    "notes": "note",
    "decisions": "decision",
    "improved": "improve",
    "improves": "improve",
    "improving": "improve",
    "readings": "reading",
    "comprehension": "understand",
    "understanding": "understand",
    "understands": "understand",
    "learned": "learn",
    "learning": "learn",
    "risks": "risk",
    "limits": "limit",
    "sources": "source",
}

NEGATION_TOKENS = {"not", "never", "no", "without", "neither", "nor"}

PREDICATE_HINTS = {
    "always", "better", "cause", "false", "guarantee", "harm", "help",
    "improve", "increase", "limit", "prevent", "reduce", "risk", "true",
    "understand", "useful", "waste", "worse",
}


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    raw = re.findall(r"[a-z0-9]+", text.lower().replace("’", "'"))
    tokens = [CANONICAL.get(token, token) for token in raw]
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def topic_tokens(text: str) -> list[str]:
    return list(dict.fromkeys(tokenize(text)))


def has_negation(text: str) -> bool:
    tokens = tokenize(text, keep_stopwords=True)
    return any(token in NEGATION_TOKENS for token in tokens)


def claim_has_negative_polarity(text: str, anchors: set[str]) -> bool:
    """Return the dominant local polarity around claim predicate tokens."""
    tokens = tokenize(text, keep_stopwords=True)
    negative = positive = 0
    for index, token in enumerate(tokens):
        if token not in anchors:
            continue
        window = tokens[max(0, index - 3) : index]
        if any(value in NEGATION_TOKENS for value in window):
            negative += 1
        else:
            positive += 1
    return negative > positive


def excerpt(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"
