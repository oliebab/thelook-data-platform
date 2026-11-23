
import json
from pathlib import Path

from reporting.build_prompt import build_prompt, TEMPLATE_PATH
from reporting.llm import generate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "contracts" / "kpi_weekly.example.json"


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


if __name__ == "__main__":
    main()
