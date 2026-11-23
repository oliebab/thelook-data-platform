# dbt — TheLook Data Platform

Transforms the raw TheLook tables (`raw_thelook`) into clean, tested models in BigQuery.

**Owners:** Gabriel and Olivier

## How to run

Run every command from this folder:

```bash
cd ~/code/thelook-data-platform/dbt
poetry run dbt debug                 # check your profile and the BigQuery connection
poetry run dbt build -s <selector>   # run + test, e.g. -s staging, -s stg_orders, -s core
poetry run dbt source freshness      # check how recent the raw loads are
```

Each person needs a profile in `~/.dbt/profiles.yml` (outside the repo, never committed), with the profile name `thelook`, `method: oauth`, project `thelook-dp-2611`, location `US`.

## Targets

| Target | Dataset | Who uses it |
|---|---|---|
| `dev` (default) | `dbt_<yourname>` (e.g. `dbt_gabriel`) | everyone, for development |
| `prod` | `analytics` | only Airflow (`--target prod`) |

Never run `--target prod` by hand.

## Folder layout

```
dbt/
├── dbt_project.yml
├── models/
│   ├── staging/     sources.yml, stg_*.sql, schema.yml — views   (Gabriel; stg_events: Olivier)
│   ├── core/        fct_*, dim_*, mart_category_weekly — tables   (Gabriel)
│   ├── behaviour/   fct_sessions, fct_funnel_daily — tables       (Olivier)
│   └── kpi/         mart_kpi_weekly — tables                      (Olivier)
├── tests/           custom tests written as SQL
└── analyses/        exploration queries (Olivier)
```

Staging models are views (cheap, always fresh); everything else is materialised as a table. This is set per folder in `dbt_project.yml`.