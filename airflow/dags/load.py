from datetime import datetime, UTC

import polars as pl

from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.sdk import get_current_context

from config import TABLES_JOIN

import logging

logger = logging.getLogger(__name__)


def enrich_parquet_files(
    bucket: str,
    table: str,
    min_date: str | None,
    max_date: str | None,
    gcp_conn_id: str = "google_cloud_default",
):
    context = get_current_context()
    ds = context["ds"]

    ingestion_time = datetime.now(UTC)

    source_prefix = f"raw/{table}/run_date={ds}/"
    blob_prefix = f"staging/{table}/run_date={ds}/"
    destination_prefix = f"gs://{bucket}/{blob_prefix}"

    gcs = GCSHook(gcp_conn_id=gcp_conn_id)

    source_files = gcs.list(
        bucket_name=bucket,
        prefix=source_prefix,
    )

    for source_file in source_files:
        if not source_file.endswith(".parquet"):
            continue

        filename = source_file.split("/")[-1]

        source_uri = f"gs://{bucket}/{source_file}"
        destination_uri = destination_prefix + filename

        df = pl.read_parquet(source_uri, credential_provider=pl.CredentialProviderGCP())

        if table not in TABLES_JOIN:
            logger.info(f"Len before: {len(df)}")
            if min_date is not None:
                logger.info(f"Min_date for {table}: {min_date}")
                df = df.filter(pl.col("created_at") > pl.lit(min_date).str.to_date())

            if max_date is not None:
                logger.info(f"Max_date for {table}: {max_date}")
                df = df.filter(pl.col("created_at") <= pl.lit(max_date).str.to_date())
            logger.info(f"Len after: {len(df)}")

            df = df.with_columns(pl.col("created_at").dt.date().alias("_dt"))

        df = df.with_columns(
            [
                pl.lit(ingestion_time).alias("_ingested_at"),
                pl.lit(source_uri).alias("_source_file"),
            ]
        )

        df.write_parquet(
            destination_uri,
            credential_provider=pl.CredentialProviderGCP(),
        )
