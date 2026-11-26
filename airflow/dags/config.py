import os
import pendulum

from datetime import timedelta

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
BQ_LOCATION = os.environ["BQ_LOCATION"]
SOURCE_PROJECT = os.environ["SOURCE_PROJECT"]
SOURCE_DATASET = os.environ["SOURCE_DATASET"]
SOURCE_LOCATION = os.environ["SOURCE_LOCATION"]
DESTINATION_DATASET = os.environ["RAW_DATASET"]

CUTOFF_DATE = pendulum.datetime(2026, 11, 22, tz="UTC")
DEMO_END_DATE = pendulum.datetime(2026, 11, 26, tz="UTC")

# Temporary fix for presentation (move all table as permanant)
TABLES_PERM = [
    "users",
    "orders",
    "order_items",
    "events",
    "products",
    "distribution_centers",
    "inventory_items",
]

TABLES = [*TABLES_PERM]

DEFAULT_ARGS = {
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
