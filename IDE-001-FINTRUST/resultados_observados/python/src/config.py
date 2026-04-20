from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    debug: bool = Field(default=False, alias="DEBUG")

    gcp_project_id: str = Field(alias="GCP_PROJECT_ID")
    bq_location: Optional[str] = Field(default=None, alias="BQ_LOCATION")

    google_application_credentials: Optional[str] = Field(
        default=None, alias="GOOGLE_APPLICATION_CREDENTIALS"
    )

    bq_dataset_raw: str = Field(alias="BQ_DATASET_RAW")
    bq_dataset_clean: str = Field(alias="BQ_DATASET_CLEAN")
    bq_dataset_rejects: Optional[str] = Field(default=None, alias="BQ_DATASET_REJECTS")
    bq_dataset_datamart: str = Field(alias="BQ_DATASET_DATAMART")

    # Raw table names
    bq_table_customers: str = Field(default="customers", alias="BQ_TABLE_CUSTOMERS")
    bq_table_loans: str = Field(default="loans", alias="BQ_TABLE_LOANS")
    bq_table_installments: str = Field(default="installments", alias="BQ_TABLE_INSTALLMENTS")
    bq_table_payments: str = Field(default="payments", alias="BQ_TABLE_PAYMENTS")

    # Optional incremental watermarks (column names in raw tables)
    customers_watermark_col: str = Field(default="created_at", alias="CUSTOMERS_WATERMARK_COL")
    loans_watermark_col: str = Field(default="origination_date", alias="LOANS_WATERMARK_COL")
    installments_watermark_col: str = Field(default="due_date", alias="INSTALLMENTS_WATERMARK_COL")
    payments_watermark_col: str = Field(default="loaded_at", alias="PAYMENTS_WATERMARK_COL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
