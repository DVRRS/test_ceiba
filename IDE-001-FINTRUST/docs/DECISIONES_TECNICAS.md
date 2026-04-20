# Decisiones Técnicas, Supuestos y Riesgos Conocidos

**Proyecto**: Pipeline de Limpieza y Datamart - FinTrust
**Fecha**: Abril 19, 2026
**Versión**: 1.0

---

## 📐 1. Decisiones Técnicas

### 1.1 Arquitectura de Datos

#### **Decisión**: Arquitectura de 3 capas (Raw → Clean → Datamart)

**Razones**:
- ✅ **Separación de responsabilidades**: Cada capa tiene un propósito claro
- ✅ **Auditoría**: Raw preserva datos originales sin modificar
- ✅ **Flexibilidad**: Podemos reconstruir Clean/Datamart desde Raw
- ✅ **Performance**: Datamart optimizado para consultas analíticas

**Alternativas consideradas**:
- ❌ Dos capas (Raw → Clean/Datamart híbrido): Mezclaba responsabilidades
- ❌ Transformaciones in-place: No permitía auditoría ni rollback

**Impacto**:
- Mayor costo de almacenamiento (+30% aprox)
- Mayor complejidad operacional
- Mejor mantenibilidad y trazabilidad

---

### 1.2 Tecnología Stack

#### **Decisión**: FastAPI + BigQuery + Python

**Razones**:
- ✅ **FastAPI**: API moderna, async, auto-documentada (OpenAPI/Swagger)
- ✅ **BigQuery**: Serverless, escalable, optimizado para analítica, SQL estándar
- ✅ **Python**: Lenguaje conocido por el equipo, rico ecosistema de librerías

**Alternativas consideradas**:
- ❌ Airflow/Prefect: Overhead innecesario para 2 rutas simples
- ❌ SQL Server/PostgreSQL: Menos eficiente para analítica masiva

**Impacto**:
- Menor curva de aprendizaje
- Costos predecibles (BigQuery on-demand o reserva)
- Fácil integración con ecosistema GCP

---

### 1.3 Carga Incremental con MERGE

#### **Decisión**: Usar `MERGE` en BigQuery para carga incremental

**Razones**:
- ✅ **Eficiencia**: Solo actualiza registros que cambiaron
- ✅ **Idempotencia**: Ejecutar 2 veces produce mismo resultado
- ✅ **Auditoría**: Tracking de inserts/updates/deletes

**Implementación**:
```sql
MERGE target T
USING (deduped source) S
ON T.pk = S.pk
WHEN MATCHED AND (data changed using IS DISTINCT FROM) 
  THEN UPDATE
WHEN NOT MATCHED 
  THEN INSERT
```

**Alternativas consideradas**:
- ❌ DELETE + INSERT: No permite auditoría de cambios
- ❌ TRUNCATE + INSERT: Ventana de tiempo sin datos
- ❌ Append-only con particiones: Complejidad en queries

**Limitaciones**:
- MERGE no soporta DELETE en esta implementación (decisión de negocio)
- Requiere PK única

---

### 1.4 Data Quality Gating (Rejects)

#### **Decisión**: Validar ANTES de cargar + crear tabla de rejects

**Razones**:
- ✅ **Prevención**: Datos malos nunca llegan a Clean
- ✅ **Transparencia**: Rejects con columna `_reason_` explicativa
- ✅ **Auditoría**: Historial de registros rechazados

**Flujo**:
```
Raw Data
  ↓
[Business Rules Filter] → Rejects (business_rules)
  ↓
[PK Null Check] → Rejects (pk_null)
  ↓
[FK Validation] → Rejects (fk_invalid)
  ↓
[MERGE to Clean]
  ↓
[Post-Load DQ Checks] → API response (dq_pass)
```

**Alternativas consideradas**:
- ❌ Solo post-load checks: Datos malos ya están en Clean
- ❌ Logs en archivos: Difícil de consultar y analizar

**Impacto**:
- Mayor confianza en calidad de datos
- Facilita debugging y corrección en origen
- Costo adicional de storage para rejects (~5-10% de raw)

---

### 1.5 Datamart: Tablas + Vistas

#### **Decisión**: Mantener versiones materializadas (tablas) Y vistas

**Razones**:
- ✅ **Tablas**: Performance para reportes frecuentes (BI/dashboards)
- ✅ **Vistas**: Datos siempre frescos para análisis ad-hoc
- ✅ **Flexibilidad**: Usuario elige según necesidad

**Estructura**:
```
Tablas (materializadas):
- table_installments_master
- table_loans_summary
- table_payments_detail

Vistas (tiempo real):
- view_installments_master
- view_view_loans_summary
- view_payments_detail
```

**Alternativas consideradas**:
- ❌ Solo vistas: Lento para dashboards
- ❌ Solo tablas: Datos desactualizados para análisis en tiempo real

**Impacto**:
- Duplicación de código SQL (manageable con templating)
- Mayor costo de storage (~50% más en datamart)
- Mejor experiencia de usuario

---

### 1.6 CREATE OR REPLACE vs TRUNCATE

#### **Decisión**: Usar `CREATE OR REPLACE TABLE` para tablas del datamart

**Razones**:
- ✅ **Atomicidad**: Si falla, tabla vieja permanece
- ✅ **Sin downtime**: No hay ventana de tabla vacía
- ✅ **Cambio de esquema**: Permite agregar/quitar columnas fácilmente

**Alternativas consideradas**:
- ❌ TRUNCATE + INSERT: Ventana de tiempo sin datos
- ❌ MERGE incremental: Complejidad innecesaria para full refresh diario

**Limitación conocida**:
- Procesa todos los datos cada vez (no incremental)
- Aceptable para volúmenes actuales (<10M registros)

**Cuándo reconsiderar**:
- Si el refresh tarda >10 minutos
- Si necesitas refrescar cada hora (no diariamente)
- Si el volumen supera 50M registros

---

### 1.7 Infraestructura Cloud (Cloud Run + BigQuery)

#### **Decisión**: Desplegar API en Cloud Run + BigQuery como almacén

**Razones**:
- ✅ **Serverless**: Sin gestión de servidores, auto-scaling automático
- ✅ **Costo-efectivo**: Solo pagas por uso real
- ✅ **Integración nativa**: Cloud Run + BigQuery en mismo ecosistema GCP
- ✅ **Deployment simple**: `gcloud run deploy` desde Docker image
- ✅ **Seguridad**: IAM + service accounts + Secret Manager

**Arquitectura**:
```
Internet → Cloud Run (FastAPI) → BigQuery (raw/clean/datamart datasets)
                ↑
        Cloud Scheduler (trigger automático diario)
```

**Recomendación: Orquestación con Cloud Scheduler**:
- **Trigger automático**: Programa `/clean/run` y `/datamart/run` diariamente
- **Ejemplo**: `0 6 * * *` (6:00 AM todos los días)
- **Monitoring**: Integración con Cloud Logging + alertas en caso de fallos
- **Costo**: Insignificante (~$0.10/mes para 2 jobs diarios)

**Alternativas consideradas**:
- ❌ **Kubernetes (GKE)**: Overhead innecesario para 2 rutas simples
- ❌ **Cloud Functions**: Timeout de 9 min puede ser insuficiente
- ❌ **Compute Engine (VM)**: Requiere gestión manual, no auto-scaling
- ❌ **Cron manual**: No resiliente, requiere servidor siempre encendido

**Impacto**:
- Despliegue en minutos vs horas (comparado con VM/Kubernetes)
- Escalabilidad automática de 0 a N instancias
- Costos variables según uso real

---

### 1.8 Uso de IA en el Desarrollo

#### **Decisión**: Código generado y asistido por IA (Cursor)

**Razones**:
- ✅ **Velocidad**: Desarrollo ~3x más rápido
- ✅ **Calidad**: Sugerencias de best practices, validaciones, tests
- ✅ **Documentación**: Generación automática de docstrings, READMEs con lectura y correcciones
- ✅ **Refactoring**: Detección de duplicación, optimización de código

**Áreas donde IA contribuyó**:
1. **SQL dinámico**: Generación de queries MERGE con `IS DISTINCT FROM`
2. **Data Quality Rules**: Validaciones de FK, rangos, nulls
3. **Tests**: Estructura de tests unitarios (`pytest`)
4. **Documentación técnica**: Decisiones, supuestos, riesgos
5. **Optimización**: Reducción de `clean_service.py` de 937 → 688 líneas

**Validación humana aplicada**:
- ✅ Revisión de lógica de negocio (tasas, montos, FK)
- ✅ Validación de queries SQL generadas
- ✅ Testing manual de endpoints FastAPI, corrección de alucinaciones.
- ✅ Revisión y estructuración de arquitectura y de costos y performance de BigQuery

**Limitaciones conocidas**:
- ⚠️ IA puede "alucinar" nombres de tablas/columnas inexistentes
- ⚠️ Requiere validación de supuestos de negocio
- ⚠️ No reemplaza conocimiento de dominio

**Impacto**:
- Proyecto completado en días vs semanas
- Código más consistente y documentado
- Mayor cobertura de edge cases

---

## 🤔 2. Supuestos

### 2.1 Supuestos de Datos

| Supuesto | ¿Qué Asumimos? | Impacto si es Falso | Probabilidad |
|----------|----------------|---------------------|--------------|
| **PK es único en raw** | Puede haber duplicados del mismo PK | Deduplicación maneja múltiples versiones usando watermark | Baja |
| **Watermark column es útil** | La fila con mayor `created_at/loaded_at` es la versión más reciente | Podríamos cargar versión vieja del registro | Media |
| **FK parent existe primero** | Customer se carga antes que Loan, Loan antes que Installment | Rejects capturan violaciones FK, pero rechaza datos válidos si orden es incorrecto | Media |
| **Fechas son parseables** | Fechas vienen en formato reconocible por BigQuery | `SAFE_CAST` retorna NULL, registro puede continuar o ser rechazado | Baja |
| **Montos son parseables** | Valores numéricos vienen como números o strings convertibles | `SAFE_CAST` retorna NULL, registro puede ser rechazado | Baja |
| **Volumen diario < 1M registros** | La carga diaria no excede 1 millón de registros por tabla | Performance adecuada con arquitectura actual | Alta |

### 2.2 Supuestos de Negocio

| Supuesto | ¿Qué Asumimos? | Validación Requerida | Owner |
|----------|----------------|----------------------|-------|
| **Montos negativos son errores** | Un `principal_amount < 0` o `payment_amount < 0` es incorrecto | ¿Existen devoluciones, reversos, o ajustes legítimos negativos? | Negocio/Finanzas |
| **Tasas > 200% son errores** | Una tasa de interés anual >200% es un error de captura | ¿Puede el negocio otorgar créditos con tasas válidas >200%? | Riesgo/Producto |
| **Pagos pueden exceder cuota en 1%** | Tolerancia de redondeo: un pago puede ser 1% mayor a lo debido | ¿Es 1% un umbral correcto? ¿O debería ser 0% o 5%? | Finanzas |
| **Cohorte = año-mes** | Usar `YYYY-MM` del `origination_date` es suficiente para análisis | ¿Se requiere granularidad semanal o diaria? | Analítica |
| **Refresh diario es suficiente** | Datos pueden estar desactualizados hasta 24 horas | ¿Necesitan reportes intraday o es suficiente reporte EOD? | Negocio |

### 2.3 Supuestos Técnicos

| Supuesto | ¿Qué Asumimos? | Riesgo si Falla | Mitigación Actual |
|----------|----------------|-----------------|-------------------|
| **BigQuery disponible 24/7** | El servicio de BigQuery siempre responde | Pipeline falla, datos no se actualizan | Retry logic + alertas de Cloud Monitoring |
| **Credenciales GCP seguras** | El archivo `.json` y variables de entorno no están comprometidos | Acceso no autorizado a datos sensibles | IAM restrictivo + rotación + Secret Manager |
| **Dataset Raw se actualiza externamente** | Otro sistema llena `raw` con datos frescos | Datamart muestra datos viejos sin avisar | Monitoreo de freshness + check de última fecha |
| **Python 3.11+ disponible** | El runtime de Cloud Run soporta Python 3.11+ | Deployment falla, librerías incompatibles | Docker especifica versión exacta |
| **FastAPI maneja <100 req/s** | Tráfico no excede 100 requests por segundo | Latencia alta, timeouts | Cloud Run auto-scaling + alertas de performance |

---

## ⚠️ 3. Riesgos Conocidos

**📋 Ver registro completo de riesgos**: [`RIESGOS.md`](./RIESGOS.md)

El proyecto tiene **10 riesgos identificados** distribuidos en 3 categorías:

| Categoría | Riesgos | Críticos 🔴 | Moderados 🟡 |
|-----------|---------|-------------|--------------|
| **Técnicos** | 4 | 0 | 4 |
| **Datos** | 3 | 0 | 3 |
| **Operacionales** | 3 | 2 | 1 |

### Top 3 Riesgos Críticos

1. **🔴 [O1] Falta de Monitoreo**
   - Sin alertas proactivas de fallas
   - **Acción**: Implementar Cloud Monitoring + alertas (0-30 días)

2. **🔴 [O2] Single Point of Failure (Conocimiento)**
   - Solo 1 persona conoce el pipeline
   - **Acción**: Knowledge transfer + runbook (0-30 días)

3. **🟡 [T3] Costos de BigQuery**
   - Facturación impredecible sin presupuesto
   - **Acción**: Configurar alertas de presupuesto GCP (0-30 días)

**Ver análisis detallado, mitigaciones y planes de acción en** [`RIESGOS.md`](./RIESGOS.md)

---

## 🎯 4. Trade-offs Clave

| Decisión | Ganamos | Perdemos |
|----------|---------|----------|
| **3 capas de datos** | Auditoría, flexibilidad | Storage, complejidad |
| **CREATE OR REPLACE** | Atomicidad, simplicidad | Performance incremental |
| **Tablas + Vistas** | Flexibilidad | Storage, duplicación |
| **Pre-load gating** | Calidad garantizada | Costo de rejects storage |
| **Python/FastAPI** | Simplicidad, conocido | No es "big data native" |
| **BigQuery serverless** | Escalabilidad, bajo ops | Vendor lock-in, costos variables |

---

## 📋 5. TODOs Recomendados (Priorizados)

### 🔴 Prioridad Alta
1. **Monitoreo y Alertas**: Cloud Monitoring + Slack notifications
2. **Presupuesto de GCP**: Alertas de costos en BigQuery
3. **Knowledge Transfer**: Sesión con equipo + runbook

### 🟡 Prioridad Media
4. **Schema Validation**: Pre-load check de columnas esperadas
5. **Particionamiento**: Si volumen >10M registros o refresh >10 min
6. **Enmascaramiento PII**: En tablas de rejects
7. **TTL en Rejects**: Auto-eliminar después de 90 días

### 🟢 Prioridad Baja
8. **Dependabot/Renovate**: Auto-actualizar dependencias
9. **Changelog**: Documento manual de cambios
10. **MERGE Incremental en Datamart**: Si refresh >30 min

---

## 📚 Referencias

- **Código**: `/src/services/clean_service.py`, `/src/services/datamart_service.py`
- **Tests**: `/src/tests/test_data_quality_rules.py`
- **Arquitectura BigQuery**: [Best Practices](https://cloud.google.com/bigquery/docs/best-practices)
- **FastAPI Docs**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
