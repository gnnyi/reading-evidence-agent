from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reading_evidence.agent import ask
from reading_evidence.evaluation import run_eval
from reading_evidence.ingest import ingest_corpus
from reading_evidence.models import Relation


DEFAULT_INDEX = Path(".reading-evidence/index.json")


def _print_answer(answer) -> None:
    for relation in (Relation.SUPPORT, Relation.COUNTER_EVIDENCE, Relation.RELATED):
        print(relation.value)
        items = answer.by_relation(relation)
        if not items:
            print("  (none)")
        for item in items:
            print(f"  [{item.note_id}] {item.title}")
            print(f"  {item.excerpt}")
            print(f"  Citation: {item.citation}")
            print(f"  Confidence: {item.confidence:.3f} — {item.reason}")
        print()
    print(f"NO_EVIDENCE / ABSTAIN: {'YES' if answer.abstained else 'NO'}")
    if answer.abstention_reason:
        print(f"  {answer.abstention_reason}")
    print("\nSources:")
    for item in answer.evidence:
        print(f"  - [{item.note_id}] {item.citation}")
    print("\nTrace:")
    trace = answer.trace
    print(f"  - rewritten queries: {json.dumps(trace['rewritten_queries'], ensure_ascii=False)}")
    print(f"  - candidates retrieved: {trace['candidates_retrieved']}")
    print(f"  - candidates deduplicated: {trace['candidates_deduplicated']}")
    print(f"  - relation decisions: {len(trace['relation_decisions'])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reading-evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Build a local index from .md/.txt notes")
    ingest.add_argument("corpus", type=Path)
    ingest.add_argument("--index", type=Path, default=DEFAULT_INDEX)

    ask_parser = subparsers.add_parser("ask", help="Retrieve relation-aware evidence")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    ask_parser.add_argument("--json", action="store_true", dest="as_json")

    evaluate = subparsers.add_parser("eval", help="Evaluate against an explicit public/private dataset path")
    evaluate.add_argument("--dataset", type=Path, required=True)
    evaluate.add_argument("--questions", type=Path, required=True)
    evaluate.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    evaluate.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest_corpus(args.corpus, args.index)
            print(json.dumps({"status": "INDEX_READY", "index": str(args.index), **result}, indent=2))
        elif args.command == "ask":
            answer = ask(args.question, args.index)
            if args.as_json:
                print(json.dumps(answer.to_dict(), indent=2, ensure_ascii=False))
            else:
                _print_answer(answer)
        elif args.command == "eval":
            result = run_eval(args.index, args.questions, args.dataset)
            rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
