# Test Ceiba

Repositorio de proyectos de ingeniería de datos y pipelines de análisis.

---

## 📁 Proyecto

### IDE-001-FINTRUST - Pipeline de Limpieza y construcción de Datamart

**Descripción**: Pipeline de datos para procesamiento de información de créditos de FinTrust.

**Stack Tecnológico**: FastAPI + BigQuery + Python 3.11

**Características**:
- ✅ Arquitectura de 3 capas (Raw → Clean → Datamart)
- ✅ Validaciones de calidad de datos (18 checks automáticos)
- ✅ Carga incremental con MERGEs
- ✅ Tabla de rejects con trazabilidad
- ✅ 53 tests unitarios automatizados
- ✅ Datamart optimizado para BI

**Documentación**: [`IDE-001-FINTRUST/resultados_observados/python/README.md`](./IDE-001-FINTRUST/resultados_observados/python/README.md)

---

## 🏗️ Arquitectura General - IDE-001-FINTRUST

```
┌─────────────────┐
│  RAW DATASET    │  (BigQuery: fintrust_raw_alpha)
│  • customers    │
│  • loans        │
│  • installments │
│  • payments     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  CLEAN SERVICE (FastAPI)    │
│  • Deduplicación PK         │
│  • Validación FK            │
│  • Business rules           │
│  • Pre-load gating          │
└────────┬────────────────────┘
         │
         ├─────► ┌──────────────┐
         │       │ REJECTS      │ (Rechazos con _reason_)
         │       └──────────────┘
         ▼
┌─────────────────┐
│  CLEAN DATASET  │  (BigQuery: fintrust_clean_alpha)
│  • Deduplicated │
│  • Validated    │
│  • Incremental  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  DATAMART SERVICE           │
│  • Master views/tables      │
│  • Pre-calculated metrics   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│  DATAMART       │  (BigQuery: fintrust_datamart_alpha)
│  • 3 Tables     │
│  • 3 Views      │
└────────┬────────┘
         │
         ▼
   ┌─────────────┐
   │  Power BI   │
   │  Tableau    │
   │  Looker     │
   └─────────────┘
```

---

## 🚀 Quick Start

### 1. Clonar Repositorio

```bash
git clone <repo-url>
cd test_ceiba/IDE-001-FINTRUST/resultados_observados/python
```

### 2. Configurar Ambiente

```bash
# Crear virtual environment
python3 -m venv env
source env/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus valores GCP
```

### 3. Ejecutar Localmente

```bash
# Correr servidor FastAPI
uvicorn main:app --reload

# Ver documentación interactiva
open http://localhost:8000/docs
```

### 4. Endpoints Principales

```bash
# Limpieza de datos (Raw → Clean)
curl -X POST http://localhost:8000/clean/run \
  -H "Content-Type: application/json" \
  -d '{"run_dq": true}'

# Construcción del datamart (Clean → Datamart)
curl -X POST http://localhost:8000/datamart/run \
  -H "Content-Type: application/json" \
  -d '{"run": true}'
```

---

## 📊 Estructura del Proyecto IDE-001-FINTRUST

```
IDE-001-FINTRUST/
├── docs/
│   ├── DECISIONES_TECNICAS.md          # Decisiones de arquitectura y supuestos
│   ├── EVIDENCIA_CALIDAD_DATOS         # Validaciones aplicadas
│   └── RESUMEN_EJECUTIVO.md            # Resumen ejecutivo de 1 página
│
├── riesgos_conocidos/
│   └── RIESGOS.md                      # Registro de riesgos conocidos
│
└── resultados_observados/
    ├── sql/                            # Esquemas raw (BigQuery DDL)
    │   ├── customers.sql
    │   ├── loans.sql
    │   ├── installments.sql
    │   └── payments.sql
    │
    ├── preguntas_caso/                 # Queries analíticas (5 queries)
    │   ├── README.md                   # Documentación de queries
    │   ├── 01_desembolso_por_dia_ciudad_segmento.sql
    │   ├── 02_recaudo_total_diario.sql
    │   ├── 03_recaudo_aplicado_a_mora.sql
    │   ├── 04_cartera_saldo_por_cohorte.sql
    │   └── 05_top10_creditos_mayor_mora.sql
    │
    └── python/                         # Pipeline FastAPI
│       ├── main.py                      # Aplicación FastAPI
│       ├── requirements.txt             # Dependencias Python
│       ├── Dockerfile                   # Imagen Docker
│       ├── deploy.sh                    # Script de deployment
│       ├── .env.example                 # Template de variables
│       ├── .gitignore                   # Archivos ignorados por Git
│       ├── .dockerignore                # Archivos ignorados por Docker
│       ├── clean_project.sh             # Script limpieza de cache
│       │
│       ├── src/
│       │   ├── config.py               # Configuración (Pydantic)
│       │   ├── database/
│       │   │   └── bigquery_client.py  # Cliente BigQuery
│       │   ├── models/
│       │   │   └── itemModel.py        # Request/Response models
│       │   ├── routes/
│       │   │   └── routes.py           # Endpoints
│       │   ├── services/
│       │   │   ├── clean_service.py    # Lógica de limpieza
│       │   │   └── datamart_service.py # Construcción datamart
│       │   ├── datamart/               # SQL construcción del datamart
│       │   │   ├── README.md
│       │   │   ├── table_installments_master.sql
│       │   │   ├── table_loans_summary.sql
│       │   │   ├── table_payments_detail.sql
│       │   │   ├── view_installments_master.sql
│       │   │   ├── view_loans_summary.sql
│       │   │   └── view_payments_detail.sql
│       │   └── tests/                  # Tests automatizados (53 tests)
│       │       ├── README.md
│       │       ├── __init__.py
│       │       ├── test_data_quality_rules.py  (29 tests)
│       │       └── test_sql_generation.py      (24 tests)
│       │
│       ├── README.md                   # Guía principal del proyecto
│       ├── VALIDACION.md               # Reporte de validaciones
│       └── DEPLOY.md                   # Guía de deployment a Cloud Run
└── bonus_LLMs/
    └── propuesta_llm.md                      # Registro de riesgos conocidos
```

---

## ✅ Validaciones Implementadas

El pipeline incluye **18 validaciones automáticas**:

### Pre-Load (Gating - Rejects)
- ✅ **Primary Keys**: PK no nula (rechazada a `_rejects`)
- ✅ **Foreign Keys**: Validación de referencias
- ✅ **Business Rules**: Montos positivos, fechas válidas, tasas 0-200%

### Post-Load (DQ Checks)
- ✅ PK NOT NULL y UNIQUE (4 tablas)
- ✅ FK válidas (3 relaciones)
- ✅ Montos negativos
- ✅ Pagos > cuota
- ✅ Fechas futuras

**Evidencia**: 53 tests unitarios (100% passing)

---

## 📊 Datamart

### 6 Objetos (3 Tablas + 3 Vistas)

**Tablas Materializadas** (Recomendadas para BI):
1. `table_installments_master` - Detalle por cuota
2. `table_loans_summary` - Agregado por crédito
3. `table_payments_detail` - Pagos individuales

**Vistas** (Datos en tiempo real):
1. `view_installments_master` - Detalle por cuota (fresca)
2. `view_loans_summary` - Agregado por crédito (fresco)
3. `view_payments_detail` - Pagos individuales (frescos)

**Métricas Clave**:
- `cohort`: Cohorte de originación (YYYY-MM)
- `amount_paid`: Total pagado
- `outstanding_balance`: Saldo pendiente
- `days_past_due`: Días de mora
- `is_overdue`: Boolean si está en mora
- `payment_to_overdue`: Si pago fue a cuota vencida

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
cd IDE-001-FINTRUST/resultados_observados/python
source env/bin/activate
pytest src/tests/ -v

# Resultado esperado: 53 tests passed
```

---

## 🐳 Docker & Deployment

### Build Local
```bash
docker build -t fintrust-pipeline .
docker run -p 8000:8000 fintrust-pipeline
```

### Deploy a Cloud Run
```bash
# Editar variables en deploy.sh
nano deploy.sh

# Ejecutar deployment
chmod +x deploy.sh
./deploy.sh
```

**Guía completa**: [`DEPLOY.md`](./IDE-001-FINTRUST/resultados_observados/python/DEPLOY.md)

---

## 📚 Documentación Completa

### Para Desarrolladores
- [`python/README.md`](./IDE-001-FINTRUST/resultados_observados/python/README.md) - Guía principal del proyecto
- [`python/EVIDENCIA_CALIDAD_DATOS.md`](./IDE-001-FINTRUST/docs/EVIDENCIA_CALIDAD_DATOS.md) - Reporte de validaciones implementadas
- [`python/DEPLOY.md`](./IDE-001-FINTRUST/resultados_observados/python/DEPLOY.md) - Guía de deployment a Cloud Run
- [`python/src/tests/README.md`](./IDE-001-FINTRUST/resultados_observados/python/src/tests/README.md) - Documentación de tests

### Para Analistas
- [`python/src/datamart/README.md`](./IDE-001-FINTRUST/resultados_observados/python/src/datamart/README.md) - Documentación del datamart
- [`preguntas_caso/README.md`](./IDE-001-FINTRUST/resultados_observados/preguntas_caso/README.md) - Queries analíticas (5 queries)

### Para Managers/Leads
- [`instrucciones_ejecucion_decisiones_clave/RESUMEN_EJECUTIVO.md`](./IDE-001-FINTRUST/instrucciones_ejecucion_decisiones_clave/RESUMEN_EJECUTIVO.md) - Resumen ejecutivo de 1 página
- [`instrucciones_ejecucion_decisiones_clave/DECISIONES_TECNICAS.md`](./IDE-001-FINTRUST/instrucciones_ejecucion_decisiones_clave/DECISIONES_TECNICAS.md) - Decisiones y supuestos

### Para Gestión de Riesgos
- [`riesgos_conocidos/RIESGOS.md`](./IDE-001-FINTRUST/riesgos_conocidos/RIESGOS.md) - Registro de riesgos conocidos (10 riesgos)

---

## 🔑 Tecnologías Utilizadas

| Tecnología | Uso | Versión |
|------------|-----|---------|
| **Python** | Lenguaje base | 3.11+ |
| **FastAPI** | Web framework | 0.104+ |
| **BigQuery** | Data warehouse | GCP |
| **Pydantic** | Validación de datos | 2.5+ |
| **pytest** | Testing | 7.4+ |
| **Docker** | Containerización | 20.10+ |
| **Cloud Run** | Deployment | GCP |

---

## 📈 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Tests** | 53 (100% passing) |
| **Cobertura DQ** | 18 checks automáticos |
| **Documentación** | 9 archivos MD |
| **Tablas procesadas** | 4 (customers, loans, installments, payments) |
| **Objetos datamart** | 6 (3 tablas + 3 vistas) |
| **Queries analíticas** | 5 queries pre-construidas |

---

## 🎯 Características Destacadas

✅ **Arquitectura de 3 Capas**: Raw → Clean → Datamart
✅ **Data Quality Gating**: Validación pre-load con rejects
✅ **Carga Incremental**: MERGE eficiente (solo actualiza cambios)
✅ **100% Datamart**: Queries analíticas autocontenidas
✅ **Tests Automatizados**: 53 tests unitarios (100% passing)
✅ **Documentación Completa**: 9 documentos técnicos
✅ **Production-Ready**: Docker + Cloud Run deployment

---

## 🔒 Seguridad

- ❌ **NUNCA** subir archivos `.env` o service account JSON al repo
- ✅ Usar `.env.example` como template
- ✅ Service account con permisos mínimos (BigQuery Data Editor + Job User)
- ✅ Dataset `rejects` separado con permisos restringidos

---

## 👥 Equipo

**Proyecto**: FinTrust - Pipeline de Análisis de Cartera
**Owner**: Bryan David Rosas
**Fecha**: Abril 2026

---

## 📝 Notas

- Las tablas del datamart se refrescan manualmente con `/datamart/run`
- Recomendado: programar refresh diario con Cloud Scheduler
- Las vistas siempre muestran datos frescos (no requieren refresh)
- Ver registro de riesgos en [`RIESGOS.md`](./IDE-001-FINTRUST/riesgos_conocidos/RIESGOS.md)

---

## 📞 Soporte

Para preguntas o issues:
1. Revisar documentación en [`IDE-001-FINTRUST/resultados_observados/python/`](./IDE-001-FINTRUST/resultados_observados/python/)
2. Consultar [`RIESGOS.md`](./IDE-001-FINTRUST/riesgos_conocidos/RIESGOS.md) para problemas conocidos
