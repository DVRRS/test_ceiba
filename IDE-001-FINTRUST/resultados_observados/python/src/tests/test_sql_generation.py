"""
Tests de integración para validar la generación de SQL.
Valida que el SQL generado tenga la estructura correcta.
"""
import os
import sys
import re
import pytest

# Configurar path para importar el módulo
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set required env vars for Settings
os.environ.setdefault("GCP_PROJECT_ID", "test-project")
os.environ.setdefault("BQ_DATASET_RAW", "raw_ds")
os.environ.setdefault("BQ_DATASET_CLEAN", "clean_ds")
os.environ.setdefault("BQ_DATASET_REJECTS", "rejects_ds")
os.environ.setdefault("BQ_DATASET_DATAMART", "datamart_ds")


class TestSelectCleanSQL:
    """Tests para validar el SQL de select_clean"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _table_spec
        self._table_spec = _table_spec

    def test_customers_select_has_where_clause(self):
        """El select de customers debe tener WHERE clause con validaciones"""
        spec = self._table_spec("customers")
        select_clean = spec["select_clean"].upper()
        
        assert "WHERE" in select_clean, "Debe tener WHERE clause"
        assert "MONTHLY_INCOME" in select_clean and ">= 0" in select_clean
        assert "1900-01-01" in select_clean

    def test_loans_select_has_business_validations(self):
        """El select de loans debe tener validaciones de negocio"""
        spec = self._table_spec("loans")
        select_clean = spec["select_clean"].upper()
        
        assert "WHERE" in select_clean
        assert "PRINCIPAL_AMOUNT" in select_clean and "> 0" in select_clean
        assert "ANNUAL_RATE" in select_clean and ">= 0" in select_clean
        assert "TERM_MONTHS" in select_clean and "> 0" in select_clean

    def test_installments_select_validates_amounts(self):
        """El select de installments debe validar que los montos sean >= 0"""
        spec = self._table_spec("installments")
        select_clean = spec["select_clean"].upper()
        
        assert "PRINCIPAL_DUE" in select_clean and ">= 0" in select_clean
        assert "INTEREST_DUE" in select_clean and ">= 0" in select_clean

    def test_payments_select_validates_amount(self):
        """El select de payments debe validar que payment_amount > 0"""
        spec = self._table_spec("payments")
        select_clean = spec["select_clean"].upper()
        
        assert "PAYMENT_AMOUNT" in select_clean and "> 0" in select_clean

    def test_all_tables_use_safe_cast(self):
        """Todas las tablas deben usar SAFE_CAST para conversiones de tipo"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            spec = self._table_spec(table)
            select_clean = spec["select_clean"].upper()
            assert "SAFE_CAST" in select_clean, f"{table} debe usar SAFE_CAST"

    def test_all_tables_use_nullif_trim(self):
        """Todas las tablas deben usar NULLIF(TRIM(...)) para strings"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            spec = self._table_spec(table)
            select_clean = spec["select_clean"].upper()
            assert "NULLIF" in select_clean and "TRIM" in select_clean, \
                f"{table} debe usar NULLIF(TRIM(...))"


class TestMergeSQL:
    """Tests para validar el SQL del MERGE"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _merge_sql_for_table
        self._merge_sql_for_table = _merge_sql_for_table

    def test_merge_has_correct_structure(self):
        """El MERGE debe tener la estructura correcta"""
        for table in ["customers", "loans", "installments", "payments"]:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "MERGE" in merge_upper, f"{table}: Debe tener MERGE"
            assert "USING" in merge_upper, f"{table}: Debe tener USING"
            assert " ON " in merge_upper, f"{table}: Debe tener ON clause"
            assert "WHEN MATCHED" in merge_upper, f"{table}: Debe tener WHEN MATCHED"
            assert "WHEN NOT MATCHED" in merge_upper, f"{table}: Debe tener WHEN NOT MATCHED"

    def test_merge_has_deduplication_logic(self):
        """El MERGE debe incluir lógica de deduplicación con ROW_NUMBER"""
        for table in ["customers", "loans", "installments", "payments"]:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "ROW_NUMBER()" in merge_upper, f"{table}: Debe usar ROW_NUMBER() para dedup"
            assert "PARTITION BY" in merge_upper, f"{table}: Debe particionar por PK"

    def test_merge_has_change_condition(self):
        """El MERGE debe tener condición de cambio con IS DISTINCT FROM"""
        for table in ["customers", "loans", "installments", "payments"]:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "IS DISTINCT FROM" in merge_upper, \
                f"{table}: Debe usar IS DISTINCT FROM para detectar cambios"

    def test_merge_filters_by_fk_for_dependent_tables(self):
        """El MERGE de tablas dependientes debe filtrar por FK válidas"""
        dependent_tables = ["loans", "installments", "payments"]
        
        for table in dependent_tables:
            _, merge_sql = self._merge_sql_for_table(table)
            # Debe tener algún filtro de FK (puede ser en el WHERE o NOT EXISTS)
            assert "NOT EXISTS" in merge_sql.upper() or \
                   ("WHERE" in merge_sql.upper() and "IS NOT NULL" in merge_sql.upper()), \
                   f"{table}: Debe filtrar por FK válidas"

    def test_merge_inserts_new_records(self):
        """El MERGE debe insertar nuevos registros"""
        for table in ["customers", "loans", "installments", "payments"]:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "INSERT" in merge_upper, f"{table}: Debe tener INSERT para nuevos registros"

    def test_merge_updates_existing_records(self):
        """El MERGE debe actualizar registros existentes"""
        for table in ["customers", "loans", "installments", "payments"]:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "UPDATE SET" in merge_upper, f"{table}: Debe tener UPDATE para registros existentes"


class TestDQChecksSQL:
    """Tests para validar los DQ checks SQL"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _dq_checks_sql
        self._dq_checks_sql = _dq_checks_sql

    def test_dq_checks_are_generated(self):
        """Se deben generar DQ checks"""
        checks = self._dq_checks_sql()
        assert len(checks) > 0, "Debe haber al menos un DQ check"

    def test_dq_checks_have_name_and_sql(self):
        """Cada DQ check debe tener nombre y SQL"""
        checks = self._dq_checks_sql()
        
        for check_name, check_sql in checks:
            assert isinstance(check_name, str), "El nombre debe ser string"
            assert isinstance(check_sql, str), "El SQL debe ser string"
            assert len(check_name) > 0, "El nombre no puede estar vacío"
            assert len(check_sql) > 0, "El SQL no puede estar vacío"

    def test_dq_checks_count_violations(self):
        """Cada DQ check debe contar violations (SELECT COUNT(1))"""
        checks = self._dq_checks_sql()
        
        for check_name, check_sql in checks:
            check_upper = check_sql.upper()
            assert "SELECT" in check_upper, f"{check_name}: Debe tener SELECT"
            assert "COUNT" in check_upper, f"{check_name}: Debe contar violations"

    def test_pk_not_null_checks_exist(self):
        """Debe haber checks de PK NOT NULL para todas las tablas"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        expected_pk_checks = [
            "customers_pk_not_null",
            "loans_pk_not_null",
            "installments_pk_not_null",
            "payments_pk_not_null",
        ]
        
        for expected in expected_pk_checks:
            assert expected in check_names, f"Debe existir check {expected}"

    def test_pk_unique_checks_exist(self):
        """Debe haber checks de PK UNIQUE para todas las tablas"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        expected_unique_checks = [
            "customers_pk_unique",
            "loans_pk_unique",
            "installments_pk_unique",
            "payments_pk_unique",
        ]
        
        for expected in expected_unique_checks:
            assert expected in check_names, f"Debe existir check {expected}"

    def test_fk_checks_exist(self):
        """Debe haber checks de FK para relaciones entre tablas"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        expected_fk_checks = [
            "loans_customer_fk",
            "installments_loan_fk",
            "payments_installment_fk",
        ]
        
        for expected in expected_fk_checks:
            assert expected in check_names, f"Debe existir check {expected}"

    def test_negative_amounts_checks_exist(self):
        """Debe haber checks de montos negativos"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        negative_checks = [
            "loans_negative_amounts",
            "installments_negative_amounts",
            "payments_negative_amounts",
            "customers_negative_income",
        ]
        
        for expected in negative_checks:
            assert expected in check_names, f"Debe existir check {expected}"

    def test_payments_exceeds_installment_check_exists(self):
        """Debe existir check de pagos > cuota"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        assert "payments_exceeds_installment" in check_names, \
            "Debe existir check payments_exceeds_installment"

    def test_future_dates_checks_exist(self):
        """Debe haber checks de fechas futuras"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        future_checks = ["loans_future_origination", "payments_future_date"]
        
        for expected in future_checks:
            assert expected in check_names, f"Debe existir check {expected}"


class TestRejectsTableSQL:
    """Tests para validar el SQL de las tablas de rejects"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _ensure_rejects_table_sql
        self._ensure_rejects_table_sql = _ensure_rejects_table_sql

    def test_rejects_table_has_reason_column(self):
        """La tabla de rejects debe tener columna _reason_"""
        for table in ["customers", "loans", "installments", "payments"]:
            sql = self._ensure_rejects_table_sql(table)
            sql_upper = sql.upper()
            
            assert "_REASON_" in sql_upper, f"{table}_rejects debe tener columna _reason_"
            assert "STRING" in sql_upper, f"_reason_ debe ser STRING"

    def test_rejects_table_has_same_columns_as_original(self):
        """La tabla de rejects debe tener las mismas columnas que la original"""
        for table in ["customers", "loans", "installments", "payments"]:
            sql = self._ensure_rejects_table_sql(table)
            sql_upper = sql.upper()
            
            # Verificar que tenga algunas columnas clave de cada tabla
            if table == "customers":
                assert "CUSTOMER_ID" in sql_upper
            elif table == "loans":
                assert "LOAN_ID" in sql_upper and "CUSTOMER_ID" in sql_upper
            elif table == "installments":
                assert "INSTALLMENT_ID" in sql_upper and "LOAN_ID" in sql_upper
            elif table == "payments":
                assert "PAYMENT_ID" in sql_upper and "INSTALLMENT_ID" in sql_upper

    def test_rejects_table_uses_create_table_if_not_exists(self):
        """La tabla de rejects debe usar CREATE TABLE IF NOT EXISTS"""
        for table in ["customers", "loans", "installments", "payments"]:
            sql = self._ensure_rejects_table_sql(table)
            sql_upper = sql.upper()
            
            assert "CREATE TABLE IF NOT EXISTS" in sql_upper, \
                f"{table}_rejects debe usar CREATE TABLE IF NOT EXISTS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
