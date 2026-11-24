
import pytest

from reporting.build_prompt import build_prompt, TEMPLATE_PATH


def test_build_prompt_replaces_json_placeholder():
    data = {"revenue": 100, "profit": 25}
    template = "Review this data:\n{{JSON}}"

    result = build_prompt(data, template)

    assert '"revenue": 100' in result
    assert '"profit": 25' in result
    assert "{{JSON}}" not in result


def test_build_prompt_preserves_unicode():
    data = {"company": "München"}
    template = "{{JSON}}"

    result = build_prompt(data, template)

    assert "München" in result


def test_build_prompt_raises_if_placeholder_missing():
    data = {"revenue": 100}
    template = "Review this data."

    with pytest.raises(
        ValueError,
        match="template has no {{JSON}} placeholder",
    ):
        build_prompt(data, template)
