import sys
from collections.abc import Sequence


def passes_gate(
    scope_result: str, relevance: str, job_results: Sequence[str]
) -> bool:
    if scope_result != "success":
        return False
    if relevance == "false":
        return True
    return (
        relevance == "true"
        and bool(job_results)
        and all(result == "success" for result in job_results)
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) < 3:
        return 2
    scope_result, relevance, *job_results = arguments
    return 0 if passes_gate(scope_result, relevance, job_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
