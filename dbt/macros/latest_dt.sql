{#
  Returns the latest snapshot date of a raw_thelook table as a literal,
  e.g. date '2026-11-23', resolved at compile time so BigQuery can prune
  partitions. Airflow runs dbt after each load, so the date stays current.

  Because the date is baked into the view at build time, a dev view keeps
  pointing at the snapshot it was built on until you rebuild it.

  Fails the build if the raw table is empty, so tests never pass on 0 rows.
#}
{% macro latest_dt(table_name) %}
  {% if execute %}
    {% set q %}select max(dt) from {{ source('thelook_raw', table_name) }}{% endset %}
    {% set latest = run_query(q).columns[0][0] %}
    {% if latest is none %}
      {{ exceptions.raise_compiler_error("raw_thelook." ~ table_name ~ " is empty") }}
    {% endif %}
    {{ return("date '" ~ latest ~ "'") }}
  {% else %}
    {{ return("current_date()") }}
  {% endif %}
{% endmacro %}
