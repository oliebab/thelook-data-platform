from datetime import date

import pytest

from reporting.fetch_kpis import KPIS, build_payload, pct_change, pts_change


def make_kpi_row(**overrides):
    row = {"week_start": date(2026, 11, 16), "week_end": date(2026, 11, 22)}
    for name, _unit in KPIS:
        row[f"{name}_current"] = 100.0
        row[f"{name}_previous"] = 100.0
        row[f"{name}_year_ago"] = None
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("current", "base", "expected"),
    [
        (110, 100, 10.0),
        (95, 100, -5.0),
        (100, 0, None),
        (None, 100, None),
        (100, None, None),
    ],
)
def test_pct_change(current, base, expected):
    assert pct_change(current, base) == expected


def test_pts_change_is_a_difference_not_a_ratio():
    assert pts_change(6.2, 8.9) == -2.7


def test_rates_get_points_and_amounts_get_percent():
    payload = build_payload(make_kpi_row(), [], [], is_latest_week=False)
    assert "wow_change_pts" in payload["kpis"]["return_rate"]
    assert "wow_change_pct" not in payload["kpis"]["return_rate"]
    assert "wow_change_pct" in payload["kpis"]["net_revenue"]


def test_highlight_thresholds():
    row = make_kpi_row(
        net_revenue_current=105.0,  # +5.0% -> highlight
        orders_current=104.9,  # +4.9% -> no highlight
        return_rate_current=99.0,  # -1.0 pt -> highlight
        cancellation_rate_current=99.5,  # -0.5 pt -> no highlight
    )
    kpis = build_payload(row, [], [], is_latest_week=False)["kpis"]
    assert kpis["net_revenue"]["highlight"] is True
    assert kpis["orders"]["highlight"] is False
    assert kpis["return_rate"]["highlight"] is True
    assert kpis["cancellation_rate"]["highlight"] is False


def test_missing_year_ago_stays_null():
    kpis = build_payload(make_kpi_row(), [], [], is_latest_week=False)["kpis"]
    assert kpis["sessions"]["year_ago"] is None
    assert kpis["sessions"]["yoy_change_pct"] is None


def test_channels_categories_and_latest_week_note():
    channels = [
        {
            "traffic_source": "Email",
            "sessions_current": 110,
            "sessions_previous": 100,
            "session_conversion_rate_current": 65.8,
        }
    ]
    categories = [
        {
            "net_revenue_rank": 1,
            "category": "Jeans",
            "net_revenue_current": 102.0,
            "net_revenue_previous": 100.0,
        }
    ]
    payload = build_payload(make_kpi_row(), channels, categories, is_latest_week=True)
    assert payload["channels"][0] == {
        "traffic_source": "Email",
        "sessions": 110,
        "sessions_wow_change_pct": 10.0,
        "session_conversion_rate": 65.8,
        "highlight": True,
    }
    assert payload["top_categories"][0]["highlight"] is False
    assert payload["period_start"] == "2026-11-16"
    assert len(payload["notes"]) == 3