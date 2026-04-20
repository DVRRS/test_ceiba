from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from src.config import get_settings
from src.database.bigquery_client import ensure_dataset, query

logger = logging.getLogger("datamart_service")


def _load_sql_file(filename: str) -> str:
    """Load SQL file from datamart directory."""
    sql_path = Path(__file__).parent.parent / "datamart" / filename
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def _replace_sql_placeholders(sql_template: str) -> str:
    """Replace placeholders in SQL with actual config values."""
    s = get_settings()
    return sql_template.format(
        project_id=s.gcp_project_id,
        clean_dataset=s.bq_dataset_clean,
        datamart_dataset=s.bq_dataset_datamart,
    )


def run_datamart_build() -> Dict[str, Any]:
    """
    Build/refresh datamart tables and views.
    
    Creates 6 objects:
    TABLES (materializadas, más rápidas):
    1. table_installments_master: Tabla detallada por installment
    2. table_loans_summary: Tabla agregada por loan
    3. table_payments_detail: Tabla de pagos individuales con contexto completo
    
    VIEWS (siempre datos frescos):
    4. view_installments_master: Vista detallada por installment
    5. view_loans_summary: Vista agregada por loan
    6. view_payments_detail: Vista de pagos individuales con contexto completo
    
    Recomendación: Usar las TABLAS para reportes (más rápidas), refrescar diariamente.
    Usar las VISTAS para datos en tiempo real.
    """
    s = get_settings()

    logger.info(
        "Starting datamart build (clean=%s datamart=%s)",
        s.bq_dataset_clean,
        s.bq_dataset_datamart,
    )

    ensure_dataset(s.bq_dataset_datamart)
    logger.info("Ensured datamart dataset exists: %s", s.bq_dataset_datamart)

    sql_files = [
        # Vista base requerida por payments_detail
        "view_installments_master.sql",   # Vista detallada por installment (base)
        
        # Tablas materializadas (más rápidas, refrescar periódicamente)
        "table_installments_master.sql",  # Tabla detallada por installment
        "table_loans_summary.sql",        # Tabla agregada por loan
        "table_payments_detail.sql",      # Tabla de pagos individuales (usa view_installments_master)
        
        # Vistas adicionales (siempre datos frescos)
        "view_loans_summary.sql",         # Vista agregada por loan (usa view_installments_master)
        "view_payments_detail.sql",       # Vista de pagos individuales (usa view_installments_master)
    ]

    results: List[Dict[str, Any]] = []

    for sql_file in sql_files:
        logger.info("Executing datamart SQL: %s", sql_file)
        
        sql_template = _load_sql_file(sql_file)
        sql_final = _replace_sql_placeholders(sql_template)
        
        job = query(sql_final)
        job.result()
        
        # Extract table/view name from filename
        table_name = sql_file.replace(".sql", "")
        
        results.append({
            "table": table_name,
            "job_id": job.job_id,
            "status": "success",
        })
        
        logger.info("Completed datamart table/view: %s (job_id=%s)", table_name, job.job_id)

    logger.info("Datamart build completed successfully")

    return {
        "dataset_datamart": s.bq_dataset_datamart,
        "tables_created": [r["table"] for r in results],
        "jobs": results,
        "status": "completed",
    }
