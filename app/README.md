# app: Streamlit app (owners: Gabriel)

Presents the weekly KPIs, the LLM business review, and the funnel and channels, read from BigQuery.

## Pages

`Home.py` is the entry point: it sets up the page and the Plotly template, shows the
navigation bar and the sidebar (week selector shared by every page through
`st.session_state["week"]`), then runs the selected page.

| Page | Reads |
|---|---|
| `pages/overview.py` | `mart_kpi_weekly`, review headline |
| `pages/1_KPIs.py` | `mart_kpi_weekly`, `mart_category_weekly` |
| `pages/2_Review.py` | `reports.llm_business_review` (selected week; passed reviews first) |
| `pages/3_Funnel_and_channels.py` | `fct_funnel_daily`, `mart_channel_weekly` |

- `data.py`: every BigQuery query, one function per query, parameterised and cached for an hour.
- `ui.py`: shared UI (sidebar, header, Plotly template, KPI cards, friendly error messages).
- `.streamlit/config.toml`: theme. Streamlit reads it from the folder it is started in, so run it from `app/`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `APP_DATASET` | `analytics` | dataset of the dbt marts |
| `APP_REPORTS_TABLE` | `thelook-dp-2611.reports.llm_business_review` | LLM review table |

No credentials file: on the VM, the BigQuery client uses the VM's service account.

## How to run

As a service (reads `analytics`, the prod dataset):

```bash
cd ~/code/thelook-data-platform/airflow
docker compose up -d --build streamlit
```

The app is published on `127.0.0.1:8501` only: forward port 8501 in VS Code (Ports tab).
After a prod run, `docker compose restart streamlit` clears the one-hour query cache.

For development, against a dev dataset (run from `app/` so the theme is applied):

```bash
cd ~/code/thelook-data-platform/app
APP_DATASET=dbt_olivier poetry run streamlit run Home.py --server.port 8502
```

Use port 8502 so it doesn't clash with the service on 8501.

## Notes

- Rates are stored as 0-100 percentages; their changes are shown in points.
- The last loaded day of `fct_funnel_daily` is marked provisional: sessions continuing past midnight aren't loaded yet.
- Package versions in `Dockerfile` are pinned to `poetry.lock`. Update both together.
