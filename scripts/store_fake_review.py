from datetime import date

from reporting.store import store

store(
    period_type="week",
    period_start=date(2026, 11, 16),
    period_end=date(2026, 11, 22),
    model="fake-model",
    prompt_version="test-0",
    input_json={
        "period_type": "week",
        "period_start": "2026-11-16",
        "period_end": "2026-11-22",
        "kpis": {"net_revenue": {"current": 1000.0, "previous": 900.0, "year_ago": None,
                                 "unit": "EUR", "wow_change_pct": 11.1, "yoy_change_pct": None}},
        "top_categories": [],
    },
    output_md="Headline: FAKE review, test row only.",
    guardrail_passed=True,
)