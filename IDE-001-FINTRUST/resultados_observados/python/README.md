# Pipeline de Limpieza y Análisis de Cartera - FinTrust

FastAPI + BigQuery para procesamiento de datos financieros con calidad garantizada.

---

## 📋 ¿Qué Hace?

Pipeline de 3 capas que:
1. **Limpia** datos raw (validaciones + deduplicación)
2. **Carga** incrementalmente a `clean` con `MERGE`
3. **Construye** datamart para análisis (tablas + vistas)

---

## 🏗️ Arquitectura

```
RAW (4 tablas)
  ↓
[Clean Service] → Rejects
  ↓
CLEAN (4 tablas)
  ↓
[Datamart Service]
  ↓
DATAMART (6 objetos: 3 tablas + 3 vistas)
  ↓
Power BI / Tableau
```

**Endpoints**:
- `POST /clean/run` → Limpia y carga incremental
- `POST /datamart/run` → Construye/refresca datamart

---

## 📁 Estructura

```
python/
├── main.py                        # FastAPI app
├── requirements.txt               # Dependencias
├── .env.example                   # Template de configuración
├── Dockerfile                     # Imagen Docker
├── .dockerignore                  # Exclusiones para Docker
├── deploy.sh                      # Script de deploy
├── DEPLOY.md                      # Guía de deployment
│
└── src/
    ├── config.py                  # Configuración
    ├── routes/routes.py           # Endpoints
    ├── services/
    │   ├── clean_service.py       # Limpieza + MERGE
    │   └── datamart_service.py    # Datamart
    ├── datamart/                  # 6 archivos SQL
    │   ├── table_installments_master.sql
    │   ├── table_loans_summary.sql
    │   ├── table_payments_detail.sql
    │   ├── view_installments_master.sql
    │   ├── view_loans_summary.sql
    │   └── view_payments_detail.sql
    └── tests/                     # 53 tests unitarios
        ├── test_data_quality_rules.py
        └── test_sql_generation.py
```

---

## 🚀 Quick Start

```bash
# 1. Setup
python3 -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Editar con tus variables

# 2. Run
uvicorn main:app --reload

# 3. Test
open http://localhost:8000/docs
```

---

## 📡 Endpoints

### `POST /clean/run`
Limpia y carga incremental (raw → clean).

```bash
curl -X POST http://localhost:8000/clean/run \
  -H "Content-Type: application/json" \
  -d '{"run_dq": true}'
```

**Respuesta**:
```json
{
  "tables_merged": ["customers", "loans", "installments", "payments"],
  "merge_results": {"customers": {"inserted": 10, "updated": 5}},
  "dq_pass": true,
  "status": "completed"
}
```

### `POST /datamart/run`
Construye/refresca datamart (clean → datamart).

```bash
curl -X POST http://localhost:8000/datamart/run \
  -H "Content-Type: application/json" \
  -d '{"run": true}'
```

**Respuesta**:
```json
{
  "tables_created": [
    "table_installments_master",
    "table_loans_summary",
    "table_payments_detail",
    "view_installments_master",
    "view_loans_summary",
    "view_payments_detail"
  ],
  "status": "completed"
}
```

---

## ✅ Validaciones

| Tipo | Qué Valida |
|------|------------|
| **Negocio** | Montos positivos, fechas válidas (1900-hoy), tasas 0-200% |
| **PKs** | No nulas, únicas (deduplicación), última versión (watermark) |
| **FKs** | `loans.customer_id`, `installments.loan_id`, `payments.installment_id` |
| **DQ Checks** | 17+ checks post-merge (PKs, FKs, montos, pagos > cuota, fechas futuras) |

**Ver detalle**: [`../../docs/EVIDENCIA_CALIDAD_DATOS.md`](../../docs/EVIDENCIA_CALIDAD_DATOS.md)

---

## 🧪 Tests

```bash
pytest src/tests/ -v  # 53 tests unitarios
```

**Validan**: Reglas de negocio, generación SQL, MERGE, DQ checks.
**Ver**: [`src/tests/README.md`](./src/tests/README.md)

---

## 📊 Datamart

**6 objetos** = 3 tablas (rápidas para BI) + 3 vistas (datos frescos).

| Objeto | Granularidad | Campos Clave |
|--------|--------------|--------------|
| `installments_master` | Por cuota | `amount_paid`, `outstanding_balance`, `days_past_due`, `is_overdue` |
| `loans_summary` | Por crédito | `total_outstanding`, `overdue_balance`, `risk_category` |
| `payments_detail` | Por pago | `payment_to_overdue`, `payment_on_time`, `payment_days_after_due` |

**Ver queries**: [`src/datamart/README.md`](./src/datamart/README.md)

---

## 🐳 Docker

```bash
docker build -t fintrust-pipeline .
docker run -p 8000:8000 --env-file .env fintrust-pipeline
```

---

## ☁️ Deployment

```bash
chmod +x deploy.sh && ./deploy.sh
```

**Ver guía completa**: [`DEPLOY.md`](./DEPLOY.md)

---

## 📚 Documentación

| Archivo | Descripción |
|---------|-------------|
| [`DEPLOY.md`](./DEPLOY.md) | Deployment a Cloud Run |
| [`src/tests/README.md`](./src/tests/README.md) | Tests unitarios |
| [`src/datamart/README.md`](./src/datamart/README.md) | Datamart y queries |
| [`../../docs/EVIDENCIA_CALIDAD_DATOS.md`](../../docs/EVIDENCIA_CALIDAD_DATOS.md) | Validaciones implementadas |
| [`../../docs/DECISIONES_TECNICAS.md`](../../docs/DECISIONES_TECNICAS.md) | Decisiones de arquitectura |
| [`../../docs/RESUMEN_EJECUTIVO.md`](../../docs/RESUMEN_EJECUTIVO.md) | Resumen ejecutivo |
| [`../../riesgos_conocidos/RIESGOS.md`](../../riesgos_conocidos/RIESGOS.md) | Riesgos y mitigaciones |

---

## 📦 Stack Técnico

FastAPI + BigQuery + Pydantic + pytest + Docker + Cloud Run

---

## 🔒 Seguridad

- ❌ NUNCA subir `.env` o service account `.json`
- ✅ Service account con permisos mínimos (BigQuery Data Editor + Job User)

---

## 📝 Notas

- Tablas del datamart: refresh manual con `POST /datamart/run`
- Recomendado: Cloud Scheduler diario
- Vistas: siempre frescos (no requieren refresh)
