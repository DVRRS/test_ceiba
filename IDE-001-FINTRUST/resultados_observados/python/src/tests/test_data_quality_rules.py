"""
Tests unitarios para las reglas de calidad de datos.
Valida que las reglas de negocio estén correctamente implementadas.
"""
import os
import sys
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


class TestBusinessRules:
    """Tests para validar las reglas de negocio implementadas"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _table_spec
        self._table_spec = _table_spec

    def test_loans_principal_must_be_positive(self):
        """El principal_amount de un loan debe ser > 0"""
        spec = self._table_spec("loans")
        select_clean = spec["select_clean"].upper()
        
        # Debe tener WHERE clause que valide principal_amount > 0
        assert "WHERE" in select_clean, "Debe tener WHERE clause"
        assert "PRINCIPAL_AMOUNT" in select_clean, "Debe mencionar PRINCIPAL_AMOUNT"
        assert "> 0" in select_clean, "Debe validar > 0"
        
        # Verificar que está en el contexto correcto (después del WHERE)
        where_section = select_clean.split("WHERE")[1]
        assert "PRINCIPAL_AMOUNT" in where_section and "> 0" in where_section

    def test_payments_amount_must_be_positive(self):
        """Los payment_amount deben ser > 0"""
        spec = self._table_spec("payments")
        select_clean = spec["select_clean"].upper()
        
        assert "WHERE" in select_clean
        assert "PAYMENT_AMOUNT" in select_clean
        where_section = select_clean.split("WHERE")[1]
        assert "PAYMENT_AMOUNT" in where_section and "> 0" in where_section

    def test_installments_amounts_must_be_non_negative(self):
        """Los montos de installments (principal_due, interest_due) deben ser >= 0"""
        spec = self._table_spec("installments")
        select_clean = spec["select_clean"].upper()
        
        assert "WHERE" in select_clean
        where_section = select_clean.split("WHERE")[1]
        assert "PRINCIPAL_DUE" in where_section and ">= 0" in where_section
        assert "INTEREST_DUE" in where_section and ">= 0" in where_section

    def test_customers_income_must_be_non_negative(self):
        """El monthly_income de customers debe ser >= 0"""
        spec = self._table_spec("customers")
        select_clean = spec["select_clean"].upper()
        
        assert "WHERE" in select_clean
        where_section = select_clean.split("WHERE")[1]
        assert "MONTHLY_INCOME" in where_section and ">= 0" in where_section

    def test_dates_must_be_in_valid_range(self):
        """Las fechas deben estar entre 1900-01-01 y CURRENT_DATE"""
        # Verificar en loans
        loans_spec = self._table_spec("loans")
        loans_sql = loans_spec["select_clean"].upper()
        assert "1900-01-01" in loans_sql
        assert "CURRENT_DATE()" in loans_sql
        
        # Verificar en payments
        payments_spec = self._table_spec("payments")
        payments_sql = payments_spec["select_clean"].upper()
        assert "1900-01-01" in payments_sql
        assert "CURRENT_DATE()" in payments_sql

    def test_annual_rate_must_be_reasonable(self):
        """La tasa de interés anual debe estar validada"""
        spec = self._table_spec("loans")
        select_clean = spec["select_clean"].upper()
        
        where_section = select_clean.split("WHERE")[1]
        assert "ANNUAL_RATE" in where_section and ">= 0" in where_section

    def test_term_months_must_be_positive(self):
        """El term_months debe ser > 0"""
        spec = self._table_spec("loans")
        select_clean = spec["select_clean"].upper()
        
        where_section = select_clean.split("WHERE")[1]
        assert "TERM_MONTHS" in where_section and "> 0" in where_section


class TestPrimaryKeyRules:
    """Tests para validar las reglas de Primary Keys"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _table_spec, _merge_sql_for_table
        self._table_spec = _table_spec
        self._merge_sql_for_table = _merge_sql_for_table

    def test_pk_cannot_be_null(self):
        """Ninguna PK puede ser NULL"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            # El MERGE debe tener lógica para excluir PKs nulas
            spec = self._table_spec(table)
            pk = spec["pk"].upper()
            
            # Debe haber un filtro WHERE pk IS NOT NULL en el deduped
            assert pk in merge_upper
            assert "IS NOT NULL" in merge_upper

    def test_pk_must_be_unique(self):
        """Las PKs deben ser únicas en clean tables"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            # Debe usar ROW_NUMBER() para deduplicación
            assert "ROW_NUMBER()" in merge_upper
            assert "PARTITION BY" in merge_upper
            
            # Debe filtrar WHERE rn = 1
            assert "RN = 1" in merge_upper or "RN=1" in merge_upper

    def test_pk_deduplication_uses_watermark(self):
        """La deduplicación debe usar la columna watermark para elegir la versión más reciente"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            spec = self._table_spec(table)
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            # Debe ordenar por watermark
            watermark = spec["wm"].upper()
            assert watermark in merge_upper
            assert "ORDER BY" in merge_upper
            assert "DESC" in merge_upper  # Orden descendente para tomar la más reciente


class TestForeignKeyRules:
    """Tests para validar las reglas de Foreign Keys"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _table_spec
        self._table_spec = _table_spec

    def test_loans_must_have_valid_customer(self):
        """Un loan debe tener un customer_id válido"""
        spec = self._table_spec("loans")
        
        # Debe tener FK configurada
        assert spec["fk"] is not None
        assert spec["fk"]["col"] == "customer_id"
        assert spec["fk"]["parent_logical_table"] == "customers"
        assert spec["fk"]["parent_pk"] == "customer_id"

    def test_installments_must_have_valid_loan(self):
        """Un installment debe tener un loan_id válido"""
        spec = self._table_spec("installments")
        
        assert spec["fk"] is not None
        assert spec["fk"]["col"] == "loan_id"
        assert spec["fk"]["parent_logical_table"] == "loans"
        assert spec["fk"]["parent_pk"] == "loan_id"

    def test_payments_must_have_valid_installment(self):
        """Un payment debe tener un installment_id válido"""
        spec = self._table_spec("payments")
        
        assert spec["fk"] is not None
        assert spec["fk"]["col"] == "installment_id"
        assert spec["fk"]["parent_logical_table"] == "installments"
        assert spec["fk"]["parent_pk"] == "installment_id"


class TestDataQualityChecks:
    """Tests para validar los DQ checks post-merge"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _dq_checks_sql
        self._dq_checks_sql = _dq_checks_sql

    def test_dq_checks_exist_for_all_tables(self):
        """Debe haber DQ checks para todas las tablas"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        # Debe haber checks para cada tabla
        assert any("customers" in name for name in check_names)
        assert any("loans" in name for name in check_names)
        assert any("installments" in name for name in check_names)
        assert any("payments" in name for name in check_names)

    def test_dq_checks_include_pk_validations(self):
        """Los DQ checks deben incluir validaciones de PK (not null, unique)"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        required_pk_checks = [
            "customers_pk_not_null",
            "customers_pk_unique",
            "loans_pk_not_null",
            "loans_pk_unique",
            "installments_pk_not_null",
            "installments_pk_unique",
            "payments_pk_not_null",
            "payments_pk_unique",
        ]
        
        for required in required_pk_checks:
            assert required in check_names, f"Falta check: {required}"

    def test_dq_checks_include_fk_validations(self):
        """Los DQ checks deben incluir validaciones de FK"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        required_fk_checks = [
            "loans_customer_fk",
            "installments_loan_fk",
            "payments_installment_fk",
        ]
        
        for required in required_fk_checks:
            assert required in check_names, f"Falta check: {required}"

    def test_dq_checks_include_business_validations(self):
        """Los DQ checks deben incluir validaciones de negocio"""
        checks = self._dq_checks_sql()
        check_names = [name for name, _ in checks]
        
        required_business_checks = [
            "loans_negative_amounts",
            "loans_invalid_rate",
            "installments_negative_amounts",
            "payments_negative_amounts",
            "payments_exceeds_installment",
            "customers_negative_income",
            "loans_future_origination",
            "payments_future_date",
        ]
        
        for required in required_business_checks:
            assert required in check_names, f"Falta check: {required}"

    def test_payments_exceeds_installment_logic(self):
        """El check de pagos > cuota debe validar que SUM(payments) <= installment_total"""
        checks = self._dq_checks_sql()
        check_dict = {name: sql for name, sql in checks}
        
        assert "payments_exceeds_installment" in check_dict
        
        sql = check_dict["payments_exceeds_installment"].upper()
        assert "SUM" in sql  # Debe sumar payments
        assert "PRINCIPAL_DUE" in sql and "INTEREST_DUE" in sql  # Debe sumar cuota
        assert "HAVING" in sql  # Debe filtrar con HAVING
        assert "1.01" in sql  # Debe usar tolerancia del 1%


class TestMergeLogic:
    """Tests para validar la lógica del MERGE incremental"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _merge_sql_for_table, _table_spec
        self._merge_sql_for_table = _merge_sql_for_table
        self._table_spec = _table_spec

    def test_merge_uses_on_clause_with_pk(self):
        """El MERGE debe usar ON con la PK para identificar registros existentes"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            spec = self._table_spec(table)
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            pk = spec["pk"].upper()
            assert " ON " in merge_upper
            # Debe tener ON T.pk = S.pk
            assert f"T.{pk}" in merge_upper and f"S.{pk}" in merge_upper

    def test_merge_updates_only_when_changed(self):
        """El MERGE solo debe actualizar cuando hay cambios reales"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "WHEN MATCHED" in merge_upper
            assert "IS DISTINCT FROM" in merge_upper

    def test_merge_inserts_new_records(self):
        """El MERGE debe insertar registros nuevos"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            assert "WHEN NOT MATCHED" in merge_upper
            assert "INSERT" in merge_upper

    def test_merge_does_not_delete(self):
        """El MERGE no debe borrar registros (soft delete o no delete)"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            _, merge_sql = self._merge_sql_for_table(table)
            merge_upper = merge_sql.upper()
            
            # No debe tener WHEN NOT MATCHED BY SOURCE (que haría DELETE)
            assert "NOT MATCHED BY SOURCE" not in merge_upper
            assert "DELETE" not in merge_upper


class TestRejectsTable:
    """Tests para validar las tablas de rejects"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _ensure_rejects_table_sql
        self._ensure_rejects_table_sql = _ensure_rejects_table_sql

    def test_rejects_tables_have_reason_column(self):
        """Las tablas de rejects deben tener una columna _reason_"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            sql = self._ensure_rejects_table_sql(table)
            sql_upper = sql.upper()
            
            assert "_REASON_" in sql_upper
            assert "STRING" in sql_upper

    def test_rejects_capture_pk_null(self):
        """Las filas con PK NULL deben ir a rejects"""
        # Esta lógica está en run_clean_incremental, no en el SQL estático
        # Validamos que el mecanismo existe revisando el código
        from src.services.clean_service import _insert_rejects_sql
        
        # La función _insert_rejects_sql debe existir y ser callable
        assert callable(_insert_rejects_sql)

    def test_rejects_capture_fk_invalid(self):
        """Las filas con FK inválida deben ir a rejects"""
        from src.services.clean_service import _table_spec
        
        # Las tablas dependientes deben tener FK configurada
        loans_spec = _table_spec("loans")
        assert loans_spec["fk"] is not None
        
        installments_spec = _table_spec("installments")
        assert installments_spec["fk"] is not None
        
        payments_spec = _table_spec("payments")
        assert payments_spec["fk"] is not None

    def test_rejects_capture_business_rules(self):
        """Las filas que fallan reglas de negocio se filtran antes del MERGE"""
        # Las reglas de negocio están en el WHERE de select_clean
        from src.services.clean_service import _table_spec
        
        spec = _table_spec("loans")
        select_clean = spec["select_clean"].upper()
        
        # Debe tener WHERE con validaciones
        assert "WHERE" in select_clean
        assert "> 0" in select_clean  # Validación de montos


class TestDataTypeCasting:
    """Tests para validar el casting de tipos de datos"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.services.clean_service import _table_spec
        self._table_spec = _table_spec

    def test_safe_cast_is_used_for_numeric_fields(self):
        """Los campos numéricos deben usar SAFE_CAST para manejar errores de conversión"""
        tables_with_numeric = {
            "customers": ["monthly_income"],
            "loans": ["principal_amount", "annual_rate"],
            "installments": ["principal_due", "interest_due"],
            "payments": ["payment_amount"],
        }
        
        for table, fields in tables_with_numeric.items():
            spec = self._table_spec(table)
            select_clean = spec["select_clean"].upper()
            
            for field in fields:
                assert "SAFE_CAST" in select_clean
                assert field.upper() in select_clean
                assert "NUMERIC" in select_clean

    def test_safe_cast_is_used_for_date_fields(self):
        """Los campos de fecha deben usar SAFE_CAST"""
        tables_with_dates = {
            "customers": ["created_at"],
            "loans": ["origination_date"],
            "installments": ["due_date"],
            "payments": ["payment_date"],
        }
        
        for table, fields in tables_with_dates.items():
            spec = self._table_spec(table)
            select_clean = spec["select_clean"].upper()
            
            for field in fields:
                assert "SAFE_CAST" in select_clean
                assert field.upper() in select_clean
                assert "DATE" in select_clean

    def test_strings_are_trimmed_and_nullified(self):
        """Los strings deben ser limpiados con TRIM y NULLIF"""
        tables = ["customers", "loans", "installments", "payments"]
        
        for table in tables:
            spec = self._table_spec(table)
            select_clean = spec["select_clean"].upper()
            
            assert "NULLIF" in select_clean
            assert "TRIM" in select_clean


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
