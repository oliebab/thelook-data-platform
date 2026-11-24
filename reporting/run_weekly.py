"""Weekly review job: fetch -> build the prompt -> generate -> guardrail -> store.

    poetry run python -m reporting.run_weekly --week-start 2026-11-16

Without --week-start it reviews the latest complete week. If the guardrail finds numbers
that are not in the input, the review is still stored (guardrail_passed = false, useful to
debug) and the job exits with code 1, so Airflow marks the task as failed.
"""

import argparse
import os
import sys
from datetime import date

from reporting.build_prompt import TEMPLATE_PATH, build_prompt
from reporting.fetch_kpis import fetch_week
from reporting.guardrail import check_numbers
from reporting.llm import generate
from reporting.store import store

PROMPT_VERSION = (
    TEMPLATE_PATH.stem
)  # "weekly_review_v1": changes when the template file changes


def run(week_start: date | None = None) -> bool:
    data = fetch_week(week_start)
    prompt = build_prompt(data, TEMPLATE_PATH.read_text(encoding="utf-8"))
    output_md = generate(prompt)
    unexpected = check_numbers(output_md, data)

    store(
        period_type="week",
        period_start=date.fromisoformat(data["period_start"]),
        period_end=date.fromisoformat(data["period_end"]),
        model=os.environ["GEMINI_MODEL"],
        prompt_version=PROMPT_VERSION,
        input_json=data,
        output_md=output_md,
        guardrail_passed=not unexpected,
    )

    print(output_md)
    print(f"\nStored review for week {data['period_start']} ({PROMPT_VERSION}).")
    if unexpected:
        print(
            f"GUARDRAIL FAILED: numbers not in the input: {unexpected}", file=sys.stderr
        )
        return False
    print("Guardrail passed.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate, check and store the weekly business review."
    )
    parser.add_argument(
        "--week-start", type=date.fromisoformat, help="Monday of the week, YYYY-MM-DD"
    )
    args = parser.parse_args()
    if not run(args.week_start):
        sys.exit(1)


if __name__ == "__main__":
    main()