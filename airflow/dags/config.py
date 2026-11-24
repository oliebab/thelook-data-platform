import os
import pendulum

from datetime import datetime, timedelta

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
BQ_LOCATION = os.environ["BQ_LOCATION"]
SOURCE_PROJECT = os.environ["SOURCE_PROJECT"]
SOURCE_DATASET = os.environ["SOURCE_DATASET"]
SOURCE_LOCATION = os.environ["SOURCE_LOCATION"]
DESTINATION_DATASET = os.environ["DESTINATION_DATASET"]

CUTOFF_DATE = pendulum.datetime(2026, 11, 22, tz="UTC")

TABLES_JOIN = [
    "products",
    "distribution_centers",
]

TABLES = ["users", "orders", "order_items", "inventory_items", "events", *TABLES_JOIN]

DEFAULT_ARGS = {
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
