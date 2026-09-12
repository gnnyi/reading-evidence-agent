from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reading_evidence.agent import DEFAULT_MAX_PER_RELATION, ask
from reading_evidence.evaluation import run_eval
from reading_evidence.ingest import ingest_corpus
from reading_evidence.judge import DeepSeekJudge, JudgeError, LexicalJudge, RelationJudge
from reading_evidence.judge_evaluation import run_judge_eval
from reading_evidence.models import Relation


DEFAULT_INDEX = Path(".reading-evidence/index.json")
JUDGE_CHOICES = ("lexical", "deepseek")


def _positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _add_judge_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--judge", choices=JUDGE_CHOICES, default="lexical")
    parser.add_argument(
        "--confirm-public-data",
        action="store_true",
        help="Confirm that all data sent to a remote judge is public and permitted",
    )


def _build_judge(name: str, *, confirm_public_data: bool) -> RelationJudge:
    if name == "lexical":
        return LexicalJudge()
    if not confirm_public_data:
        raise ValueError("--confirm-public-data is required when --judge deepseek")
    return DeepSeekJudge()


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
    hidden = sum(
        decision.get("drop_reason") == "max_per_relation"
        for decision in trace.get("candidate_decisions", [])
    )
    if hidden:
        print(f"  - additional evidence hidden: {hidden}; increase --max-per-relation to review it")


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
    ask_parser.add_argument(
        "--max-per-relation",
        type=_positive_integer,
        default=DEFAULT_MAX_PER_RELATION,
        metavar="N",
        help="Show up to N items per relation (default: %(default)s); does not change retrieval or abstention",
    )
    _add_judge_arguments(ask_parser)

    evaluate = subparsers.add_parser("eval", help="Evaluate against an explicit public/private dataset path")
    evaluate.add_argument("--dataset", type=Path, required=True)
    evaluate.add_argument("--questions", type=Path, required=True)
    evaluate.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    evaluate.add_argument("--output", type=Path)
    _add_judge_arguments(evaluate)

    judge_evaluate = subparsers.add_parser(
        "judge-eval",
        help="Evaluate a relation judge against a candidate-level dataset",
    )
    judge_evaluate.add_argument("--dataset", type=Path, required=True)
    judge_evaluate.add_argument("--output", type=Path)
    _add_judge_arguments(judge_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest_corpus(args.corpus, args.index)
            print(json.dumps({"status": "INDEX_READY", "index": str(args.index), **result}, indent=2))
        elif args.command == "ask":
            judge = _build_judge(
                args.judge,
                confirm_public_data=args.confirm_public_data,
            )
            answer = ask(
                args.question, args.index,
                max_per_relation=args.max_per_relation, judge=judge,
            )
            if args.as_json:
                print(json.dumps(answer.to_dict(), indent=2, ensure_ascii=False))
            else:
                if answer.status == "JUDGE_ERROR":
                    print(
                        f"error: judge failed: {answer.abstention_reason or 'unknown error'}",
                        file=sys.stderr,
                    )
                else:
                    _print_answer(answer)
            if answer.status == "JUDGE_ERROR":
                return 3
        elif args.command == "eval":
            judge = _build_judge(
                args.judge,
                confirm_public_data=args.confirm_public_data,
            )
            result = run_eval(args.index, args.questions, args.dataset, judge=judge)
            rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
        elif args.command == "judge-eval":
            judge = _build_judge(
                args.judge,
                confirm_public_data=args.confirm_public_data,
            )
            result = run_judge_eval(args.dataset, judge)
            rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
            if result["status"] == "JUDGE_ERROR":
                return 3
    except JudgeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
