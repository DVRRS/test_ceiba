from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from google.cloud import bigquery

from src.config import get_settings


@lru_cache
def get_bigquery_client() -> bigquery.Client:
    settings = get_settings()

    # If a service account JSON path is provided, rely on ADC picking it up.
    # (google-cloud-bigquery reads GOOGLE_APPLICATION_CREDENTIALS automatically)
    if settings.google_application_credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

    return bigquery.Client(project=settings.gcp_project_id)


def query(sql: str, *, location: Optional[str] = None) -> bigquery.job.QueryJob:
    settings = get_settings()
    client = get_bigquery_client()
    job_config = bigquery.QueryJobConfig()
    return client.query(sql, job_config=job_config, location=location or settings.bq_location)


def ensure_dataset(dataset_id: str, *, location: Optional[str] = None) -> None:
    settings = get_settings()
    client = get_bigquery_client()

    dataset_ref = bigquery.Dataset(f"{settings.gcp_project_id}.{dataset_id}")
    if location or settings.bq_location:
        dataset_ref.location = location or settings.bq_location

    client.create_dataset(dataset_ref, exists_ok=True)
