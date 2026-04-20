from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import bigquery

from src.config import get_settings
from src.database.bigquery_client import ensure_dataset, get_bigquery_client, query

logger = logging.getLogger("clean_service")


@dataclass(frozen=True)
class DqCheckResult:
    name: str
    violations: int


def _full_table(dataset: str, table: str) -> str:
    settings = get_settings()
    return f"`{settings.gcp_project_id}.{dataset}.{table}`"


def _rejects_dataset() -> str:
    s = get_settings()
    if not s.bq_dataset_rejects:
        raise ValueError(
            "Missing BQ_DATASET_REJECTS. Set it in .env to enable rejects gating."
        )
    return s.bq_dataset_rejects


def _rejects_table_name(logical_table: str) -> str:
    return f"{logical_table}_rejects"


def _table_spec(table: str) -> Dict[str, Any]:
    """
    Centralizes per-table metadata for:
    - cleaned select
    - pk and watermark
    - reject table schema (casts)
    - optional FK rule for rejects
    """
    s = get_settings()
    raw_ds = s.bq_dataset_raw

    if table == "customers":
        return {
            "logical_table": "customers",
            "pk": "customer_id",
            "wm": s.customers_watermark_col,
            "raw_table": s.bq_table_customers,
            "clean_table": s.bq_table_customers,
            "cols": [
                "customer_id",
                "full_name",
                "city",
                "segment",
                "monthly_income",
                "created_at",
            ],
            "select_clean": f"""
              SELECT
                NULLIF(TRIM(customer_id), '') AS customer_id,
                NULLIF(TRIM(full_name), '') AS full_name,
                NULLIF(TRIM(city), '') AS city,
                NULLIF(TRIM(segment), '') AS segment,
                SAFE_CAST(monthly_income AS NUMERIC) AS monthly_income,
                SAFE_CAST(created_at AS DATE) AS created_at
              FROM {_full_table(raw_ds, s.bq_table_customers)}
              WHERE 1=1
                AND (SAFE_CAST(monthly_income AS NUMERIC) IS NULL OR SAFE_CAST(monthly_income AS NUMERIC) >= 0)
                AND (SAFE_CAST(created_at AS DATE) IS NULL OR (
                  SAFE_CAST(created_at AS DATE) >= '1900-01-01' AND
                  SAFE_CAST(created_at AS DATE) <= CURRENT_DATE()
                ))
            """,
            "reject_schema_select": """
              SELECT
                CAST(NULL AS STRING) AS customer_id,
                CAST(NULL AS STRING) AS full_name,
                CAST(NULL AS STRING) AS city,
                CAST(NULL AS STRING) AS segment,
                CAST(NULL AS NUMERIC) AS monthly_income,
                CAST(NULL AS DATE) AS created_at
            """,
            "fk": None,
        }

    if table == "loans":
        return {
            "logical_table": "loans",
            "pk": "loan_id",
            "wm": s.loans_watermark_col,
            "raw_table": s.bq_table_loans,
            "clean_table": s.bq_table_loans,
            "cols": [
                "loan_id",
                "customer_id",
                "origination_date",
                "principal_amount",
                "annual_rate",
                "term_months",
                "loan_status",
                "product_type",
            ],
            "select_clean": f"""
              SELECT
                NULLIF(TRIM(loan_id), '') AS loan_id,
                NULLIF(TRIM(customer_id), '') AS customer_id,
                SAFE_CAST(origination_date AS DATE) AS origination_date,
                SAFE_CAST(principal_amount AS NUMERIC) AS principal_amount,
                SAFE_CAST(annual_rate AS NUMERIC) AS annual_rate,
                SAFE_CAST(term_months AS INT64) AS term_months,
                NULLIF(TRIM(loan_status), '') AS loan_status,
                NULLIF(TRIM(product_type), '') AS product_type
              FROM {_full_table(raw_ds, s.bq_table_loans)}
              WHERE 1=1
                AND (SAFE_CAST(principal_amount AS NUMERIC) > 0)
                AND (SAFE_CAST(annual_rate AS NUMERIC) IS NULL OR SAFE_CAST(annual_rate AS NUMERIC) >= 0)
                AND (SAFE_CAST(term_months AS INT64) IS NULL OR SAFE_CAST(term_months AS INT64) > 0)
                AND (SAFE_CAST(origination_date AS DATE) IS NULL OR (
                  SAFE_CAST(origination_date AS DATE) >= '1900-01-01' AND
                  SAFE_CAST(origination_date AS DATE) <= CURRENT_DATE()
                ))
            """,
            "reject_schema_select": """
              SELECT
                CAST(NULL AS STRING) AS loan_id,
                CAST(NULL AS STRING) AS customer_id,
                CAST(NULL AS DATE) AS origination_date,
                CAST(NULL AS NUMERIC) AS principal_amount,
                CAST(NULL AS NUMERIC) AS annual_rate,
                CAST(NULL AS INT64) AS term_months,
                CAST(NULL AS STRING) AS loan_status,
                CAST(NULL AS STRING) AS product_type
            """,
            "fk": {
                "col": "customer_id",
                "parent_logical_table": "customers",
                "parent_pk": "customer_id",
                "reason": "loans_customer_fk",
            },
        }

    if table == "installments":
        return {
            "logical_table": "installments",
            "pk": "installment_id",
            "wm": s.installments_watermark_col,
            "raw_table": s.bq_table_installments,
            "clean_table": s.bq_table_installments,
            "cols": [
                "installment_id",
                "loan_id",
                "installment_number",
                "due_date",
                "principal_due",
                "interest_due",
                "installment_status",
            ],
            "select_clean": f"""
              SELECT
                NULLIF(TRIM(installment_id), '') AS installment_id,
                NULLIF(TRIM(loan_id), '') AS loan_id,
                SAFE_CAST(installment_number AS INT64) AS installment_number,
                SAFE_CAST(due_date AS DATE) AS due_date,
                SAFE_CAST(principal_due AS NUMERIC) AS principal_due,
                SAFE_CAST(interest_due AS NUMERIC) AS interest_due,
                NULLIF(TRIM(installment_status), '') AS installment_status
              FROM {_full_table(raw_ds, s.bq_table_installments)}
              WHERE 1=1
                AND (SAFE_CAST(principal_due AS NUMERIC) IS NULL OR SAFE_CAST(principal_due AS NUMERIC) >= 0)
                AND (SAFE_CAST(interest_due AS NUMERIC) IS NULL OR SAFE_CAST(interest_due AS NUMERIC) >= 0)
                AND (SAFE_CAST(installment_number AS INT64) IS NULL OR SAFE_CAST(installment_number AS INT64) > 0)
                AND (SAFE_CAST(due_date AS DATE) IS NULL OR SAFE_CAST(due_date AS DATE) >= '1900-01-01')
            """,
            "reject_schema_select": """
              SELECT
                CAST(NULL AS STRING) AS installment_id,
                CAST(NULL AS STRING) AS loan_id,
                CAST(NULL AS INT64) AS installment_number,
                CAST(NULL AS DATE) AS due_date,
                CAST(NULL AS NUMERIC) AS principal_due,
                CAST(NULL AS NUMERIC) AS interest_due,
                CAST(NULL AS STRING) AS installment_status
            """,
            "fk": {
                "col": "loan_id",
                "parent_logical_table": "loans",
                "parent_pk": "loan_id",
                "reason": "installments_loan_fk",
            },
        }

    if table == "payments":
        return {
            "logical_table": "payments",
            "pk": "payment_id",
            "wm": s.payments_watermark_col,
            "raw_table": s.bq_table_payments,
            "clean_table": s.bq_table_payments,
            "cols": [
                "payment_id",
                "loan_id",
                "installment_id",
                "payment_date",
                "payment_amount",
                "payment_channel",
                "payment_status",
                "loaded_at",
            ],
            "select_clean": f"""
              SELECT
                NULLIF(TRIM(payment_id), '') AS payment_id,
                NULLIF(TRIM(loan_id), '') AS loan_id,
                NULLIF(TRIM(installment_id), '') AS installment_id,
                SAFE_CAST(payment_date AS DATE) AS payment_date,
                SAFE_CAST(payment_amount AS NUMERIC) AS payment_amount,
                NULLIF(TRIM(payment_channel), '') AS payment_channel,
                NULLIF(TRIM(payment_status), '') AS payment_status,
                SAFE_CAST(loaded_at AS TIMESTAMP) AS loaded_at
              FROM {_full_table(raw_ds, s.bq_table_payments)}
              WHERE 1=1
                AND (SAFE_CAST(payment_amount AS NUMERIC) > 0)
                AND (SAFE_CAST(payment_date AS DATE) IS NULL OR (
                  SAFE_CAST(payment_date AS DATE) >= '1900-01-01' AND
                  SAFE_CAST(payment_date AS DATE) <= CURRENT_DATE()
                ))
            """,
            "reject_schema_select": """
              SELECT
                CAST(NULL AS STRING) AS payment_id,
                CAST(NULL AS STRING) AS loan_id,
                CAST(NULL AS STRING) AS installment_id,
                CAST(NULL AS DATE) AS payment_date,
                CAST(NULL AS NUMERIC) AS payment_amount,
                CAST(NULL AS STRING) AS payment_channel,
                CAST(NULL AS STRING) AS payment_status,
                CAST(NULL AS TIMESTAMP) AS loaded_at
            """,
            "fk": {
                "col": "installment_id",
                "parent_logical_table": "installments",
                "parent_pk": "installment_id",
                "reason": "payments_installment_fk",
            },
        }

    raise ValueError(f"Unsupported table: {table}")


def _ensure_rejects_table_sql(logical_table: str) -> str:
    s = get_settings()
    rejects_ds = _rejects_dataset()
    spec = _table_spec(logical_table)
    rejects_table = _rejects_table_name(logical_table)

    return f"""
    CREATE TABLE IF NOT EXISTS {_full_table(rejects_ds, rejects_table)} AS
    {spec["reject_schema_select"]},
      CAST(NULL AS STRING) AS _reason_
    LIMIT 0
    """


def _insert_rejects_sql(
    *,
    logical_table: str,
    reason_expr_sql: str,
    source: str,
    where_sql: str,
) -> str:
    s = get_settings()
    rejects_ds = _rejects_dataset()
    spec = _table_spec(logical_table)
    cols = ", ".join(spec["cols"])
    rejects_table = _rejects_table_name(logical_table)

    return f"""
    INSERT INTO {_full_table(rejects_ds, rejects_table)} ({cols}, _reason_)
    WITH cleaned AS (
      {spec["select_clean"]}
    ),
    deduped_nonnull AS (
      SELECT * EXCEPT(rn)
      FROM (
        SELECT
          cleaned.*,
          ROW_NUMBER() OVER (
            PARTITION BY {spec["pk"]}
            ORDER BY SAFE_CAST({spec["wm"]} AS TIMESTAMP) DESC NULLS LAST
          ) AS rn
        FROM cleaned
        WHERE {spec["pk"]} IS NOT NULL
      )
      WHERE rn = 1
    )
    SELECT {cols}, {reason_expr_sql} AS _reason_
    FROM {source}
    WHERE {where_sql}
    """


def _create_clean_tables_sql() -> List[str]:
    """
    Create empty clean tables using reject_schema_select from _table_spec.
    Reuses schema definitions to avoid duplication.
    """
    s = get_settings()
    clean = s.bq_dataset_clean
    tables = ["customers", "loans", "installments", "payments"]
    
    ddls = []
    for table in tables:
        spec = _table_spec(table)
        ddls.append(f"""
        CREATE TABLE IF NOT EXISTS {_full_table(clean, spec["clean_table"])} AS
        {spec["reject_schema_select"]},
          CURRENT_TIMESTAMP() AS _loaded_at
        LIMIT 0
        """)
    
    return ddls


def _merge_sql_for_table(table: str) -> Tuple[str, str]:
    """
    Returns (name, MERGE sql) for a given logical table.
    Uses _table_spec() to avoid code duplication.
    """
    s = get_settings()
    clean_ds = s.bq_dataset_clean
    spec = _table_spec(table)
    
    pk = spec["pk"]
    wm = spec["wm"]
    clean_t = spec["clean_table"]
    cols = spec["cols"]
    
    # Generate UPDATE SET dynamically (exclude PK and _loaded_at)
    update_cols = [c for c in cols if c != pk]
    update_set = ",\n          ".join([f"T.{c} = S.{c}" for c in update_cols])
    update_set += ",\n          T._loaded_at = CURRENT_TIMESTAMP()"
    
    # Generate INSERT dynamically
    insert_cols_list = cols + ["_loaded_at"]
    insert_cols = f"({', '.join(insert_cols_list)})"
    insert_vals_list = [f"S.{c}" for c in cols] + ["CURRENT_TIMESTAMP()"]
    insert_vals = f"({', '.join(insert_vals_list)})"
    
    # Generate change condition dynamically (exclude PK)
    change_conditions = [f"T.{c} IS DISTINCT FROM S.{c}" for c in update_cols]
    change_condition = " OR\n          ".join(change_conditions)
    
    # FK filter (if table has FK dependency)
    if spec["fk"]:
        fk_col = spec["fk"]["col"]
        parent_spec = _table_spec(spec["fk"]["parent_logical_table"])
        parent_pk = spec["fk"]["parent_pk"]
        fk_filter_sql = f"""
          ({fk_col} IS NULL OR EXISTS (
            SELECT 1 FROM {_full_table(clean_ds, parent_spec["clean_table"])} p
            WHERE p.{parent_pk} = deduped.{fk_col}
          ))
        """
    else:
        fk_filter_sql = "TRUE"

    merge_sql = f"""
    MERGE {_full_table(clean_ds, clean_t)} T
    USING (
      WITH cleaned AS (
        {spec["select_clean"]}
      ),
      deduped AS (
        SELECT * EXCEPT(rn)
        FROM (
          SELECT
            cleaned.*,
            ROW_NUMBER() OVER (
              PARTITION BY {pk}
              ORDER BY SAFE_CAST({wm} AS TIMESTAMP) DESC NULLS LAST
            ) AS rn
          FROM cleaned
          WHERE {pk} IS NOT NULL
        )
        WHERE rn = 1
      )
      SELECT * FROM deduped
      WHERE {fk_filter_sql}
    ) S
    ON T.{pk} = S.{pk}
    WHEN MATCHED AND (
      {change_condition}
    ) THEN UPDATE SET
      {update_set}
    WHEN NOT MATCHED THEN INSERT {insert_cols} VALUES {insert_vals}
    """

    return (table, merge_sql)


def _dq_checks_sql() -> List[Tuple[str, str]]:
    """Generate DQ checks dynamically from table specs."""
    s = get_settings()
    clean = s.bq_dataset_clean
    checks = []
    
    # Generate PK and FK checks dynamically for all tables
    tables = ["customers", "loans", "installments", "payments"]
    
    for table in tables:
        spec = _table_spec(table)
        pk = spec["pk"]
        clean_table = _full_table(clean, spec["clean_table"])
        
        # PK NOT NULL
        checks.append((
            f"{table}_pk_not_null",
            f"SELECT COUNT(1) AS v FROM {clean_table} WHERE {pk} IS NULL"
        ))
        
        # PK UNIQUE
        checks.append((
            f"{table}_pk_unique",
            f"""
            SELECT COUNT(1) AS v
            FROM (
              SELECT {pk}
              FROM {clean_table}
              GROUP BY {pk}
              HAVING COUNT(1) > 1
            )
            """
        ))
        
        # FK checks for dependent tables
        if spec["fk"]:
            fk = spec["fk"]
            parent_spec = _table_spec(fk["parent_logical_table"])
            fk_col = fk["col"]
            parent_table = _full_table(clean, parent_spec["clean_table"])
            parent_pk = fk["parent_pk"]
            
            checks.append((
                fk["reason"],
                f"""
                SELECT COUNT(1) AS v
                FROM {clean_table} child
                LEFT JOIN {parent_table} parent
                  ON child.{fk_col} = parent.{parent_pk}
                WHERE child.{fk_col} IS NOT NULL AND parent.{parent_pk} IS NULL
                """
            ))
    
    # Business rule checks (specific validations)
    checks.extend([
        (
            "loans_negative_amounts",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_loans)} WHERE principal_amount < 0",
        ),
        (
            "loans_invalid_rate",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_loans)} WHERE annual_rate < 0 OR annual_rate > 200",
        ),
        (
            "installments_negative_amounts",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_installments)} WHERE principal_due < 0 OR interest_due < 0",
        ),
        (
            "payments_negative_amounts",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_payments)} WHERE payment_amount < 0",
        ),
        (
            "customers_negative_income",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_customers)} WHERE monthly_income < 0",
        ),
        (
            "loans_future_origination",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_loans)} WHERE origination_date > CURRENT_DATE()",
        ),
        (
            "payments_future_date",
            f"SELECT COUNT(1) AS v FROM {_full_table(clean, s.bq_table_payments)} WHERE payment_date > CURRENT_DATE()",
        ),
        (
            "payments_exceeds_installment",
            f"""
            SELECT COUNT(1) AS v
            FROM (
              SELECT
                p.installment_id,
                SUM(p.payment_amount) AS total_paid,
                MAX(i.principal_due + i.interest_due) AS installment_total
              FROM {_full_table(clean, s.bq_table_payments)} p
              INNER JOIN {_full_table(clean, s.bq_table_installments)} i
                ON p.installment_id = i.installment_id
              GROUP BY p.installment_id
              HAVING SUM(p.payment_amount) > MAX(i.principal_due + i.interest_due) * 1.01
            )
            """,
        ),
    ])
    
    return checks


def run_clean_incremental(*, run_dq: bool = True) -> Dict[str, Any]:
    s = get_settings()
    run_id = str(uuid.uuid4())

    logger.info(
        "Starting clean run (raw=%s clean=%s rejects=%s run_dq=%s run_id=%s)",
        s.bq_dataset_raw,
        s.bq_dataset_clean,
        _rejects_dataset(),
        run_dq,
        run_id,
    )

    ensure_dataset(s.bq_dataset_clean)
    logger.info("Ensured dataset exists: %s", s.bq_dataset_clean)

    # Rejects dataset/tables (row-level gating)
    ensure_dataset(_rejects_dataset())
    logger.info("Ensured rejects dataset exists: %s", _rejects_dataset())
    for logical_table in ("customers", "loans", "installments", "payments"):
        job = query(_ensure_rejects_table_sql(logical_table))
        job.result()

    for ddl in _create_clean_tables_sql():
        job = query(ddl)
        job.result()
        logger.info("Ensured table (CTAS): job_id=%s", job.job_id)

    rejects: Dict[str, Dict[str, Any]] = {}

    merge_jobs: Dict[str, Dict[str, Optional[int]]] = {}
    for logical_table in ("customers", "loans", "installments", "payments"):
        spec = _table_spec(logical_table)
        rejects[logical_table] = {"rejected": 0, "reasons": {}}

        if run_dq:
            # 0) Count total raw records before filters
            raw_count_sql = f"SELECT COUNT(1) AS v FROM {_full_table(s.bq_dataset_raw, spec['raw_table'])}"
            raw_count_rows = list(get_bigquery_client().query(raw_count_sql).result())
            total_raw = int(raw_count_rows[0]["v"]) if raw_count_rows else 0
            
            # Count records after cleaning filters
            clean_count_sql = f"WITH cleaned AS ({spec['select_clean']}) SELECT COUNT(1) AS v FROM cleaned"
            clean_count_rows = list(get_bigquery_client().query(clean_count_sql).result())
            total_cleaned = int(clean_count_rows[0]["v"]) if clean_count_rows else 0
            
            filtered_by_business_rules = total_raw - total_cleaned
            if filtered_by_business_rules > 0:
                rejects[logical_table]["rejected"] += filtered_by_business_rules
                rejects[logical_table]["reasons"][f"{logical_table}_business_rules"] = filtered_by_business_rules
                logger.info(
                    "Filtered rows table=%s reason=business_rules (negative amounts, invalid dates) count=%s",
                    logical_table,
                    filtered_by_business_rules
                )
            
            # 1) Reject PK nulls (from cleaned)
            pk = spec["pk"]
            pk_null_job = query(
                _insert_rejects_sql(
                    logical_table=logical_table,
                    reason_expr_sql=f"'{logical_table}_pk_null: {spec['pk']} is NULL'",
                    source="cleaned",
                    where_sql=f"{pk} IS NULL",
                )
            )
            pk_null_job.result()
            pk_null_inserted = int(
                getattr(getattr(pk_null_job, "dml_stats", None), "inserted_row_count", 0) or 0
            )
            if pk_null_inserted:
                rejects[logical_table]["rejected"] += pk_null_inserted
                rejects[logical_table]["reasons"][f"{logical_table}_pk_null"] = pk_null_inserted
                logger.info("Rejected rows table=%s reason=%s count=%s", logical_table, f"{logical_table}_pk_null", pk_null_inserted)

            # 2) Reject FK violations (from deduped_nonnull) for dependent tables
            if spec["fk"]:
                fk = spec["fk"]
                parent_spec = _table_spec(fk["parent_logical_table"])
                fk_col = fk["col"]
                parent_pk = fk["parent_pk"]
                fk_where = f"""
                  {fk_col} IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM {_full_table(s.bq_dataset_clean, parent_spec["clean_table"])} p
                    WHERE p.{parent_pk} = deduped_nonnull.{fk_col}
                  )
                """
                fk_job = query(
                    _insert_rejects_sql(
                        logical_table=logical_table,
                        reason_expr_sql=(
                            f"'{fk['reason']}: missing ' || CAST(deduped_nonnull.{fk_col} AS STRING)"
                        ),
                        source="deduped_nonnull",
                        where_sql=fk_where,
                    )
                )
                fk_job.result()
                fk_inserted = int(
                    getattr(getattr(fk_job, "dml_stats", None), "inserted_row_count", 0) or 0
                )
                if fk_inserted:
                    rejects[logical_table]["rejected"] += fk_inserted
                    rejects[logical_table]["reasons"][fk["reason"]] = fk_inserted
                    logger.info("Rejected rows table=%s reason=%s count=%s", logical_table, fk["reason"], fk_inserted)

        name, merge_sql = _merge_sql_for_table(logical_table)
        logger.info("Running MERGE for table=%s", name)
        job = query(merge_sql)
        job.result()
        inserted = None
        updated = None
        deleted = None
        affected = None

        # BigQuery exposes DML stats for MERGE jobs
        try:
            if getattr(job, "dml_stats", None):
                inserted = int(job.dml_stats.inserted_row_count or 0)
                updated = int(job.dml_stats.updated_row_count or 0)
                deleted = int(job.dml_stats.deleted_row_count or 0)
        except Exception:
            # If stats are not available, keep them as None
            pass

        try:
            if getattr(job, "num_dml_affected_rows", None) is not None:
                affected = int(job.num_dml_affected_rows)
        except Exception:
            pass

        merge_jobs[name] = {
            "job_id": job.job_id,
            "inserted": inserted,
            "updated": updated,
            "deleted": deleted,
            "affected": affected,
        }
        logger.info(
            "MERGE completed table=%s job_id=%s inserted=%s updated=%s deleted=%s affected=%s",
            name,
            job.job_id,
            inserted,
            updated,
            deleted,
            affected,
        )

    dq_results: List[DqCheckResult] = []
    if run_dq:
        client = get_bigquery_client()
        logger.info("Running post-load data quality checks")
        for check_name, check_sql in _dq_checks_sql():
            rows = list(client.query(check_sql, location=s.bq_location).result())
            violations = int(rows[0]["v"]) if rows else 0
            dq_results.append(DqCheckResult(name=check_name, violations=violations))
            logger.info("DQ check=%s violations=%s", check_name, violations)

    result = {
        "dataset_clean": s.bq_dataset_clean,
        "dataset_rejects": _rejects_dataset(),
        "run_id": run_id,
        "tables": {
            "customers": s.bq_table_customers,
            "loans": s.bq_table_loans,
            "installments": s.bq_table_installments,
            "payments": s.bq_table_payments,
        },
        "rejects": rejects,
        "merge_jobs": merge_jobs,
        "dq": [r.__dict__ for r in dq_results],
        "dq_pass": all(r.violations == 0 for r in dq_results) if run_dq else None,
    }

    logger.info("Clean run finished dq_pass=%s", result["dq_pass"])
    return result
