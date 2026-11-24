
import pytest

from reporting.guardrail import check_numbers


def test_review_only_quotes_input_numbers():
    kpi_json = {
        "revenue": 1234.5,
        "growth": 12.35,
        "profit": 500
    }

    output_md = """
    Revenue was 1234.5, growth was 12.35%,
    and profit reached 500.
    """

    assert check_numbers(output_md, kpi_json) == []


def test_flags_number_not_in_input():
    kpi_json = {
        "revenue": 1234.5,
        "growth": 12.35
    }

    output_md = "Revenue grew 47%."

    assert check_numbers(output_md, kpi_json) == ["47"]


def test_currency_and_thousands_separators_match():
    kpi_json = {
        "revenue": 1234.5
    }

    output_md = "Revenue was $1,234.5, compared with 1234.50."

    assert check_numbers(output_md, kpi_json) == []


@pytest.mark.parametrize("quoted_value", ["12.3", "12"])
def test_rounded_values_are_accepted(quoted_value):
    kpi_json = {
        "growth": 12.35
    }

    output_md = f"Growth was {quoted_value}%."

    assert check_numbers(output_md, kpi_json) == []
