# Tests - Pipeline de Limpieza

Tests unitarios que validan reglas de negocio y generación de SQL.

---

## 📁 Archivos

| Archivo | Qué Valida |
|---------|------------|
| `test_data_quality_rules.py` | Reglas de negocio implementadas (montos, fechas, PKs, FKs) |
| `test_sql_generation.py` | Estructura del SQL generado (SELECT, MERGE, DQ checks, rejects) |

**Características**:
- ⚡ Rápidos (< 1 seg)
- 🚫 No requieren BigQuery ni credenciales
- 📚 Sirven como documentación

---

## 🚀 Ejecución

### Todos los tests
```bash
# Desde el directorio raíz del proyecto python/
pytest src/tests/ -v
```

### Tests específicos
```bash
# Solo reglas de negocio
pytest src/tests/test_data_quality_rules.py -v

# Solo generación de SQL
pytest src/tests/test_sql_generation.py -v

# Un test particular
pytest src/tests/test_data_quality_rules.py::TestBusinessRules::test_loans_principal_must_be_positive -v
```

---

## 🔍 Qué Validan

### Reglas de Negocio ✅

| Regla | Validación |
|-------|------------|
| **Montos positivos** | `principal_amount > 0`, `payment_amount > 0`, etc. |
| **Fechas válidas** | Rango 1900-01-01 hasta `CURRENT_DATE()` |
| **Primary Keys** | No nulas, únicas, deduplicación con watermark |
| **Foreign Keys** | `loans.customer_id` → `customers`, `installments.loan_id` → `loans`, etc. |
| **DQ Checks** | 17+ validaciones (PKs, FKs, montos, tasas, pagos > cuota, fechas futuras) |

### Estructura SQL ✅

| Componente | Validación |
|------------|------------|
| **SELECT** | WHERE clauses, SAFE_CAST, TRIM, NULLIF |
| **MERGE** | USING, ON, deduplicación, WHEN MATCHED/NOT MATCHED, condición de cambio |
| **Rejects** | Columna `_reason_`, misma estructura, CREATE OR REPLACE |

---

## 📊 Coverage

- ✅ 100% reglas de negocio
- ✅ 100% tablas (customers, loans, installments, payments)
- ✅ 100% DQ checks
- ✅ 100% estructuras MERGE y rejects

---

---

## 📝 Notas

- Estos tests **validan la implementación**, no ejecutan queries reales en BigQuery
- Para tests de integración real (contra BigQuery), crear `test_integration.py`
- Útil como documentación: lee los tests para entender las reglas aplicadas
