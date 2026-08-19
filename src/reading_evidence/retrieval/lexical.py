from __future__ import annotations

import math
from collections import Counter

from reading_evidence.models import Note, QueryPlan, RetrievalCandidate
from reading_evidence.text import tokenize


DEFAULT_TOP_K_PER_QUERY = 8
DEFAULT_RRF_K = 60


def _bm25(notes: list[Note], query: str) -> list[tuple[Note, float]]:
    query_tokens = tokenize(query)
    documents = [tokenize(f"{note.title} {note.text}") for note in notes]
    if not query_tokens or not documents:
        return []
    avg_length = sum(len(tokens) for tokens in documents) / len(documents)
    document_frequency = Counter(
        token for tokens in documents for token in set(tokens)
    )
    k1, b = 1.5, 0.75
    scored: list[tuple[Note, float]] = []
    for note, tokens in zip(notes, documents):
        frequencies = Counter(tokens)
        score = 0.0
        for token in sorted(set(query_tokens)):
            frequency = frequencies[token]
            if frequency == 0:
                continue
            df = document_frequency[token]
            inverse_frequency = math.log(1 + (len(notes) - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * len(tokens) / max(avg_length, 1))
            score += inverse_frequency * frequency * (k1 + 1) / denominator
        if score > 0:
            scored.append((note, score))
    return sorted(scored, key=lambda value: (-value[1], value[0].note_id))


def retrieve(
    notes: list[Note],
    plan: QueryPlan,
    *,
    top_k_per_query: int = DEFAULT_TOP_K_PER_QUERY,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[RetrievalCandidate]:
    fused: dict[str, RetrievalCandidate] = {}
    for query_index, query in enumerate(plan.as_list()):
        for rank, (note, score) in enumerate(_bm25(notes, query)[:top_k_per_query], start=1):
            candidate = fused.setdefault(
                note.note_id,
                RetrievalCandidate(note=note, rrf_score=0.0, best_lexical_score=0.0),
            )
            candidate.rrf_score += 1.0 / (rrf_k + rank)
            candidate.best_lexical_score = max(candidate.best_lexical_score, score)
            candidate.matched_queries.append(
                {"query_index": query_index, "query": query, "rank": rank, "score": round(score, 6)}
            )
    return sorted(
        fused.values(),
        key=lambda item: (-item.rrf_score, -item.best_lexical_score, item.note.note_id),
    )
