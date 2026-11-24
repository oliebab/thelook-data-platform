import json
import sys
from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reporting.guardrail import check_numbers


EXAMPLE_FILE = Path("contracts/kpi_weekly.example.json")


def generate_review(kpi_data):
    """
    Call your existing LLM prompt here.
    Return the generated Markdown review as a string.
    """

    # Replace this with your existing prompt invocation.
    raise NotImplementedError("Connect your review-generation prompt")


def main():
    with EXAMPLE_FILE.open(encoding="utf-8") as f:
        kpi_data = json.load(f)

    print("Generating review...")

    output_md = generate_review(kpi_data)

    print("\n--- GENERATED REVIEW ---\n")
    print(output_md)

    print("\n--- GUARDRAIL RESULTS ---\n")

    unexpected = check_numbers(output_md, kpi_data)

    if unexpected:
        print("GUARDRAIL FAILED")
        print(f"Unexpected numbers: {unexpected}")
    else:
        print("GUARDRAIL PASSED")

    # Save generated review for inspection
    Path("example_review.md").write_text(
        output_md,
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()