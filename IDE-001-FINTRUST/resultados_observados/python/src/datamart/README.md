# Datamart - Análisis de Cartera FinTrust

Datamart simplificado para análisis de cartera, mora y recaudo, para uso de BI.

---

## 📊 Estructura

**6 objetos** = 3 tablas materializadas + 3 vistas en tiempo real

| Tipo | Performance | Datos | Uso Recomendado |
|------|-------------|-------|-----------------|
| **Tablas** (`table_*`) | ⚡ Rápidas | Snapshot del último refresh | Reportes, dashboards, BI |
| **Vistas** (`view_*`) | 🐌 Lentas | ✅ Siempre frescos | Consultas ad-hoc, debugging |

**Regla simple**: BI → tablas. Análisis puntual → vistas.

---

## 📋 Objetos

### 1. `table_installments_master` / `view_installments_master`
Detalle a nivel de cuota (installment).

**Campos clave**:
- **IDs**: `installment_id`, `loan_id`, `customer_id`
- **Cliente**: `customer_name`, `city`, `segment`
- **Crédito**: `loan_principal`, `annual_rate`, `term_months`, `cohort`
- **Cuota**: `installment_number`, `due_date`, `principal_due`, `interest_due`
- **Métricas**: `amount_paid`, `outstanding_balance`, `is_overdue`, `days_past_due`, `mora_bucket`

---

### 2. `table_loans_summary` / `view_loans_summary`
Resumen a nivel de crédito (loan).

**Campos clave**:
- **Cuotas**: `total_installments`, `installments_paid`, `installments_overdue`
- **Montos**: `total_loan_amount`, `total_paid`, `total_outstanding`, `overdue_balance`
- **Mora**: `max_days_past_due`, `pct_overdue`
- **Riesgo**: `risk_category` (Bajo, Moderado, Alto, Crítico)

---

### 3. `table_payments_detail` / `view_payments_detail`
Detalle de pagos individuales con contexto completo.

**Campos clave**:
- **Pago**: `payment_id`, `payment_date`, `payment_amount`, `payment_channel`
- **Contexto**: `customer_name`, `city`, `segment`, `installment_number`, `due_date`
- **Flags**: `payment_to_overdue` (pagó a cuota vencida), `payment_on_time`, `payment_days_after_due`

---

---

## 🔄 Refresh

### Manual
```bash
curl -X POST http://localhost:8000/datamart/run \
  -H "Content-Type: application/json" \
  -d '{"run": true}'
```

### Automático (Cloud Scheduler)
```bash
# Diario a las 6am
gcloud scheduler jobs create http datamart-refresh \
  --schedule="0 6 * * *" \
  --uri="https://your-app.run.app/datamart/run" \
  --http-method=POST
```

---

## 📝 Notas Técnicas

**Lógica de cálculo**:
- `amount_paid`: Suma de `payments.payment_amount` por `installment_id`
- `outstanding_balance`: `(principal_due + interest_due) - amount_paid`
- `is_overdue`: `due_date < CURRENT_DATE()` AND `outstanding_balance > 0.01`
- `days_past_due`: `DATE_DIFF(CURRENT_DATE(), due_date, DAY)` (si overdue)
- `cohort`: `FORMAT_DATE('%Y-%m', origination_date)` (ej: "2024-03")

**Dependencias**:
- Consultan tablas de `clean_dataset`: `customers`, `loans`, `installments`, `payments`

---

## 🔧 Troubleshooting

| Problema | Solución |
|----------|----------|
| Vista no se crea | Verifica que `datamart_dataset` exista |
| Resultados vacíos | Verifica datos en `installments` y `payments` |
| Métricas incorrectas | Verifica FKs (`installment_id`, `loan_id`) |

---

## 📂 Archivos

```
src/datamart/
├── table_installments_master.sql
├── table_loans_summary.sql
├── table_payments_detail.sql
├── view_installments_master.sql
├── view_loans_summary.sql
└── view_payments_detail.sql
```

**Ver queries SQL listas para usar**: `/src/preguntas_caso/`
