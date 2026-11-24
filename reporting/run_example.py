
import json
import sys
from pathlib import Path

from reporting.build_prompt import TEMPLATE_PATH, build_prompt
from reporting.guardrail import check_numbers
from reporting.llm import generate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "contracts" / "kpi_weekly.example.json"
OUTPUT_PATH = PROJECT_ROOT / "example_review.md"


def main():
    with DATA_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    prompt = build_prompt(data, template)

    print("Generating weekly review...\n")

    result = generate(prompt)

    print("=" * 60)
    print("GENERATED WEEKLY REVIEW")
    print("=" * 60)
    print(result)

    # Save generated review
    OUTPUT_PATH.write_text(result, encoding="utf-8")

    print("\n" + "=" * 60)
    print("GUARDRAIL VALIDATION")
    print("=" * 60)

    unexpected_numbers = check_numbers(result, data)

    if unexpected_numbers:
        print("GUARDRAIL FAILED")
        print(f"Unexpected numbers: {unexpected_numbers}")
        print("Please review the generated Markdown.")
        sys.exit(1)

    print("GUARDRAIL PASSED")
    print("All reported numbers are supported by the input JSON.")

    print(f"\nReview saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
