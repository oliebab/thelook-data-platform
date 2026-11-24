import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "reporting" / "prompts"
# The template file name is the prompt version stored with each review.
# Default is v2; run an older one with e.g. PROMPT_VERSION=weekly_review_v1.
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "weekly_review_v2")
TEMPLATE_PATH = PROMPTS_DIR / f"{PROMPT_VERSION}.md"


def build_prompt(data, template):
    if "{{JSON}}" not in template:
        raise ValueError("template has no {{JSON}} placeholder")

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