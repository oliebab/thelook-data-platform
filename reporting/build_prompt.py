import argparse
import json
import pprint
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "reporting" / "prompts" / "weekly_review_v1.md"


def build_prompt(data, template):
    formatted_json = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
)

    return template.replace("{{JSON}}", formatted_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", nargs="?")
    args = parser.parse_args()

    if args.json_file:
        with open(args.json_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    print(build_prompt(data, template))


if __name__ == "__main__":
    main()