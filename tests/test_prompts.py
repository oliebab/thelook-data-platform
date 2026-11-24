import json

import pytest

from reporting.build_prompt import (
    PROJECT_ROOT,
    PROMPTS_DIR,
    TEMPLATE_PATH,
    build_prompt,
)

PROMPT_FILES = sorted(PROMPTS_DIR.glob("weekly_review_v*.md"))


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_every_prompt_has_exactly_one_placeholder(path):
    assert path.read_text(encoding="utf-8").count("{{JSON}}") == 1


def test_default_template_exists():
    assert TEMPLATE_PATH.exists(), f"{TEMPLATE_PATH.name} not found in {PROMPTS_DIR}"


def test_default_template_builds_with_the_example_contract():
    data = json.loads(
        (PROJECT_ROOT / "contracts" / "kpi_weekly.example.json").read_text(
            encoding="utf-8"
        )
    )
    prompt = build_prompt(data, TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert "{{JSON}}" not in prompt
    assert '"net_revenue"' in prompt