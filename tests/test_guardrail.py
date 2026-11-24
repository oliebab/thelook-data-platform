
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


def test_negative_change_written_as_fell_is_accepted():
    kpi_json = {
        "wow_change_pts": -2.7
    }

    output_md = "Return rate fell 2.7 pts."

    assert check_numbers(output_md, kpi_json) == []


def test_negative_percentage_change_written_as_fell_is_accepted():
    kpi_json = {
        "wow_change_pct": -4.6
    }

    output_md = "Net revenue fell 4.6%."

    assert check_numbers(output_md, kpi_json) == []


def test_top_three_is_ignored():
    kpi_json = {
        "revenue": 1234.5
    }

    output_md = "The top 3 products generated the most revenue."

    assert check_numbers(output_md, kpi_json) == []


def test_period_dates_are_allowed():
    kpi_json = {
        "revenue": 1234.5,
        "period_start": "2025-01-01",
        "period_end": "2025-12-31"
    }

    output_md = "Revenue was 1234.5 for 2025-01-01 to 2025-12-31."

    assert check_numbers(output_md, kpi_json) == []


def test_flags_invented_single_digit_percentage():
    kpi_json = {
        "revenue": 1234.5
    }

    output_md = "Orders up 7%."

    assert check_numbers(output_md, kpi_json) == ["7"]


def test_flags_invented_single_digit_percentage_with_verb():
    kpi_json = {
        "revenue": 1234.5
    }

    output_md = "Revenue rose 5%."

    assert check_numbers(output_md, kpi_json) == ["5"]


def test_top_three_without_percentage_is_ignored():
    kpi_json = {
        "revenue": 1234.5
    }

    output_md = "The top 3 products performed best."

    assert check_numbers(output_md, kpi_json) == []
