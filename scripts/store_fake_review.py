from datetime import date

from reporting.store import store

# Test row only: a fake week far in the past, so it can never replace a real review.
FAKE_WEEK_START = date(2000, 1, 3)
FAKE_WEEK_END = date(2000, 1, 9)


def main() -> None:
    store(
        period_type="week",
        period_start=FAKE_WEEK_START,
        period_end=FAKE_WEEK_END,
        model="fake-model",
        prompt_version="test-0",
        input_json={
            "period_type": "week",
            "period_start": "2000-01-03",
            "period_end": "2000-01-09",
            "kpis": {"net_revenue": {"current": 1000.0, "previous": 900.0, "year_ago": None,
                                     "unit": "USD", "wow_change_pct": 11.1, "yoy_change_pct": None}},
            "top_categories": [],
        },
        output_md="Headline: FAKE review, test row only.",
        guardrail_passed=True,
    )


if __name__ == "__main__":
    main()