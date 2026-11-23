
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_PATH = ROOT / "reporting/prompts/weekly_review_v1.md"


def build_prompt(json_path: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    with open(json_path, encoding="utf-8") as file:
        data = json.load(file)

    pretty_json = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )

    return template.replace("{{WEEKLY_JSON}}", pretty_json)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python reporting/build_prompt.py "
            "contracts/kpi_weekly.example.json"
        )

    print(build_prompt(sys.argv[1]))
