# Registro de Riesgos - Pipeline FinTrust

**Proyecto**: Pipeline de Limpieza y Datamart
**Fecha**: Abril 17, 2026
**Última Revisión**: Abril 17, 2026
**Próxima Revisión**: Julio 2026 (trimestral)

---

## 📊 Resumen de Riesgos

| Categoría | Riesgos Identificados | Alta | Media | Baja |
|-----------|----------------------|------|-------|------|
| **Técnicos** | 4 | 0 | 4 | 0 |
| **Datos** | 3 | 0 | 3 | 0 |
| **Operacionales** | 3 | 2 | 1 | 0 |
| **TOTAL** | 10 | 2 | 8 | 0 |

---

## ⚠️ Riesgos Técnicos

### 🟡 Riesgo T1: Performance con Alto Volumen

**Descripción**: 
- CREATE OR REPLACE procesa todos los datos cada vez (no es incremental)
- El datamart se reconstruye completamente en cada refresh

**Impacto**: 
- ⚠️ **Alto**: Refresh del datamart podría tardar >30 minutos
- Timeout en Cloud Run (máximo 60 min)
- Costos elevados de BigQuery por procesamiento completo

**Probabilidad**: 🟡 **Media** (si volumen crece >50M registros)

**Indicadores de Activación**:
- ⚠️ Refresh tarda >10 minutos
- ⚠️ Volumen de pagos >10M registros
- ⚠️ Crecimiento mensual >50%

**Mitigación**:
- ✅ **Corto plazo**: Monitorear tiempo de ejecución
- ⚠️ **Mediano plazo**: Implementar particionamiento por `payment_date`
- ⚠️ **Largo plazo**: Cambiar a MERGE incremental en datamart

**Plan de Contingencia**:
```sql
-- Opción 1: Particionamiento
CREATE OR REPLACE TABLE `table_payments_detail`
PARTITION BY DATE(payment_date)
AS SELECT ...

-- Opción 2: MERGE Incremental
MERGE table_payments_detail T
USING (SELECT ... WHERE payment_date >= CURRENT_DATE() - 7) S
ON T.payment_id = S.payment_id
...
```

---

### 🟡 Riesgo T2: Schema Drift en Raw

**Descripción**: 
- Dataset Raw cambia estructura sin aviso previo
- Columnas se renombran, eliminan o cambian de tipo

**Impacto**: 
- ⚠️ **Alto**: Pipeline falla completamente
- Queries con columnas faltantes
- Conversiones de tipo fallan

**Probabilidad**: 🟡 **Media** (depende de gobernanza en origen)

**Indicadores de Activación**:
- ⚠️ Errores "Column not found" en logs
- ⚠️ Aumento repentino de rejects sin razón aparente
- ⚠️ SAFE_CAST retorna muchos NULLs (>10%)

**Mitigación**:
- ✅ **Implementado**: Uso de `SAFE_CAST` (retorna NULL si falla)
- ✅ **Implementado**: Tests unitarios validan estructura esperada
- ⚠️ **TODO**: Schema validation pre-load

**Plan de Contingencia**:
```python
# TODO: Agregar schema validation
def validate_raw_schema(table_name):
    expected_columns = get_expected_schema(table_name)
    actual_columns = get_bigquery_schema(table_name)
    
    if expected_columns != actual_columns:
        alert_schema_drift(table_name, diff)
        raise SchemaValidationError()
```

**Owner**: Data Engineering + Data Source Owner  
**Estado**: 🟡 En riesgo (validación pendiente)

---

### 🟡 Riesgo T3: Costos de BigQuery

**Descripción**: 
- Queries escanean más datos de lo esperado
- Tablas no particionadas con full scans
- Queries analíticas sin filtros eficientes

**Impacto**: 
- ⚠️ **Medio**: Facturación elevada e impredecible
- Costos >$500/mes si no se optimiza

**Probabilidad**: 🟡 **Media**

**Indicadores de Activación**:
- ⚠️ Factura mensual >$200
- ⚠️ Queries escanean >1TB/día
- ⚠️ Crecimiento de datos >30%/mes

**Mitigación**:
- ✅ **Implementado**: Tablas materializadas evitan re-scans
- ✅ **Implementado**: Datamart optimizado para consultas
- ⚠️ **TODO**: Configurar alertas de presupuesto en GCP
- ⚠️ **TODO**: Implementar particionamiento

**Plan de Contingencia**:
```bash
# Configurar alertas de presupuesto
gcloud billing budgets create \
  --billing-account=$BILLING_ID \
  --display-name="BigQuery Budget" \
  --budget-amount=200USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

**Estimación de Costos Actual**:
- Storage: ~$20/mes (Raw + Clean + Datamart)
- Queries: ~$30/mes (on-demand, <500GB/día)
- **Total**: ~$50-100/mes

**Owner**: FinOps + Data Engineering  
**Estado**: 🟢 Bajo control (monitorear)

---

### 🟡 Riesgo T4: Dependencias de Python

**Descripción**: 
- Vulnerabilidades en librerías (FastAPI, google-cloud-bigquery)
- Breaking changes en actualizaciones
- Librerías deprecadas

**Impacto**: 
- ⚠️ **Bajo-Medio**: Seguridad comprometida o pipeline roto

**Probabilidad**: 🟡 **Media** (dependencias cambian constantemente)

**Indicadores de Activación**:
- ⚠️ GitHub Security Alerts
- ⚠️ CVE publicado en dependencias
- ⚠️ Deprecation warnings en logs

**Mitigación**:
- ✅ **Implementado**: `requirements.txt` con versiones fijas
- ⚠️ **TODO**: Configurar Dependabot o Renovate
- ⚠️ **TODO**: Escaneo periódico con `pip-audit` o `safety`

**Plan de Contingencia**:
```bash
# Escaneo manual de seguridad
pip install pip-audit
pip-audit

# O con safety
pip install safety
safety check
```

**Owner**: DevOps + Data Engineering  
**Estado**: 🟡 Monitorear (automatización pendiente)

---

## 🗄️ Riesgos de Datos

### 🟡 Riesgo D1: Datos Sensibles en Rejects

**Descripción**: 
- Tabla de rejects expone PII (nombres, ingresos, etc.)
- Posible violación de GDPR/compliance
- Acceso no controlado a datos rechazados

**Impacto**: 
- 🔴 **Alto**: Violación de privacidad, multas regulatorias

**Probabilidad**: 🟡 **Media**

**Indicadores de Activación**:
- ⚠️ Auditoría de seguridad identifica PII en rejects
- ⚠️ Usuario no autorizado accede a rejects dataset
- ⚠️ Rejects contienen >1000 registros con PII

**Mitigación**:
- ✅ **Implementado**: Dataset `rejects` separado con permisos restringidos
- ⚠️ **TODO**: Implementar enmascaramiento de PII (hash de nombres, ingresos)
- ⚠️ **TODO**: Configurar TTL de 90 días en rejects
- ⚠️ **TODO**: Política de acceso basada en roles (RBAC)

**Plan de Contingencia**:
```sql
-- Enmascaramiento de PII
SELECT
  TO_BASE64(SHA256(full_name)) AS full_name_hash,
  city,  -- OK, no es PII
  segment,  -- OK
  NULL AS monthly_income,  -- Enmascarar
  ...
```

**Owner**: Data Governance + Legal  
**Estado**: 🟡 Requiere acción

---

### 🟡 Riesgo D2: Deduplicación Incorrecta

**Descripción**: 
- Watermark column no refleja la versión más reciente del registro
- Se carga versión desactualizada
- Lógica de ROW_NUMBER() tiene bug

**Impacto**: 
- ⚠️ **Medio**: Datos incorrectos en Clean, decisiones erróneas

**Probabilidad**: 🟡 **Baja-Media**

**Indicadores de Activación**:
- ⚠️ Usuarios reportan datos "viejos" en Clean
- ⚠️ Comparación Raw vs Clean muestra discrepancias
- ⚠️ Watermark no se actualiza en Raw

**Mitigación**:
- ✅ **Implementado**: Tests unitarios validan lógica `ROW_NUMBER()`
- ✅ **Implementado**: Post-load DQ checks
- ⚠️ **TODO**: Validación de freshness (comparar watermark vs carga)
- ⚠️ **TODO**: Documentar asunción de watermark en README

**Plan de Contingencia**:
```sql
-- Query de validación
SELECT 
  pk,
  COUNT(*) AS versions,
  MAX(watermark) AS latest_version
FROM raw_table
GROUP BY pk
HAVING COUNT(*) > 1;
```

**Owner**: Data Engineering  
**Estado**: 🟢 Bajo control (tests validan)

---

### 🟡 Riesgo D3: FK Violations No Detectadas

**Descripción**: 
- Parent record se elimina después de que child ya se cargó
- Race condition entre tablas
- FK validation solo ocurre en momento de carga

**Impacto**: 
- ⚠️ **Medio**: Datos huérfanos en Clean, queries fallan

**Probabilidad**: 🟡 **Baja** (si proceso es secuencial)

**Indicadores de Activación**:
- ⚠️ Post-load DQ check reporta FK violations
- ⚠️ `dq_pass=false` en response
- ⚠️ Queries de datamart retornan menos filas de lo esperado

**Mitigación**:
- ✅ **Implementado**: Pre-load FK validation (rejects antes de cargar)
- ✅ **Implementado**: Post-load FK checks detectan violaciones
- ✅ **Implementado**: `dq_pass=false` alerta el problema
- ⚠️ **TODO**: Considerar soft deletes en lugar de hard deletes en origen

**Plan de Contingencia**:
```sql
-- Detectar FK violations post-load
SELECT COUNT(*) 
FROM clean.loans l
LEFT JOIN clean.customers c ON l.customer_id = c.customer_id
WHERE l.customer_id IS NOT NULL 
  AND c.customer_id IS NULL;
```

**Owner**: Data Engineering + Data Source Owner  
**Estado**: 🟢 Mitigado (checks implementados)

---

## 🔧 Riesgos Operacionales

### 🔴 Riesgo O1: Falta de Monitoreo

**Descripción**: 
- Fallas del pipeline pasan desapercibidas por horas/días
- Sin alertas proactivas
- Sin dashboard de salud

**Impacto**: 
- 🔴 **Crítico**: Datos desactualizados, decisiones erróneas, pérdida de confianza

**Probabilidad**: 🔴 **Alta** (actualmente sin implementar)

**Indicadores de Activación**:
- ⚠️ Usuario reporta datos desactualizados
- ⚠️ Pipeline falla sin que nadie se entere
- ⚠️ `dq_pass=false` por días sin acción

**Mitigación**:
- ⚠️ **TODO Crítico**: Implementar Cloud Monitoring
- ⚠️ **TODO Crítico**: Configurar alertas (Slack/Email)
- ⚠️ **TODO**: Dashboard de salud (Grafana/Looker)
- ⚠️ **TODO**: Healthcheck endpoint (`GET /health`)

**Plan de Acción (0-30 días)**:
```bash
# 1. Healthcheck endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "last_clean_run": get_last_run_time(),
        "last_dq_pass": get_last_dq_status()
    }

# 2. Cloud Monitoring Alert
gcloud monitoring policies create \
  --notification-channels=$SLACK_CHANNEL \
  --display-name="Pipeline Failed" \
  --condition="response_code >= 500"
```

**Métricas Clave a Monitorear**:
- Tiempo de ejecución de `/clean/run` y `/datamart/run`
- Tasa de error (5xx responses)
- `dq_pass` status
- Número de rejects por tabla
- Freshness de datos (última actualización)
s
**Owner**: DevOps + Data Engineering
**Estado**: 🔴 **CRÍTICO - Acción Inmediata Requerida**

---

### 🔴 Riesgo O2: Single Point of Failure (Conocimiento)

**Descripción**: 
- Solo 1 persona conoce el pipeline en profundidad
- Falta documentación operacional (runbooks)
- Sin plan de contingencia para ausencias

**Impacto**: 
- 🔴 **Alto**: Bloqueo operacional si esa persona no está disponible

**Probabilidad**: 🔴 **Alta** (situación actual)

**Indicadores de Activación**:
- ⚠️ Persona clave de vacaciones/enferma
- ⚠️ Pipeline falla y nadie sabe cómo arreglarlo
- ⚠️ Onboarding de nuevo miembro tarda >1 semana

**Mitigación**:
- ✅ **Implementado**: Documentación completa (README, VALIDACION.md, etc.)
- ✅ **Implementado**: Tests automatizados (53 tests)
- ⚠️ **TODO**: Sesión de knowledge transfer con equipo
- ⚠️ **TODO**: Runbook de troubleshooting
- ⚠️ **TODO**: Video/screencast de operación

**Plan de Acción (0-30 días)**:
1. **Knowledge Transfer Session** (2 horas)
   - Arquitectura del pipeline
   - Cómo ejecutar manualmente
   - Debugging común
   
2. **Crear Runbook** (`RUNBOOK.md`)
   - Qué hacer si `/clean/run` falla
   - Qué hacer si `dq_pass=false`
   - Cómo investigar rejects
   
3. **Pair Programming** (1 semana)
   - Trabajar junto a otro dev en cambios
   - Transferir conocimiento implícito

**Owner**: Data Engineering Manager  
**Estado**: 🔴 **CRÍTICO - Acción Inmediata Requerida**

---

### 🟡 Riesgo O3: Falta de Documentación de Cambios

**Descripción**: 
- Cambios al pipeline no se documentan adecuadamente
- Pérdida de contexto sobre decisiones técnicas
- Difícil rastrear cuándo/por qué se hizo un cambio

**Impacto**: 
- ⚠️ **Medio**: Regresiones, repetir errores del pasado

**Probabilidad**: 🟡 **Media**

**Indicadores de Activación**:
- ⚠️ Commit messages poco descriptivos
- ⚠️ "¿Por qué hicimos esto?" sin respuesta
- ⚠️ Cambios sin PR review

**Mitigación**:
- ✅ **Implementado**: Commits con mensajes descriptivos
- ✅ **Implementado**: Documentación técnica actualizada
- ⚠️ **TODO**: CHANGELOG.md manual
- ⚠️ **TODO**: Template de PR con secciones obligatorias
- ⚠️ **TODO**: ADRs (Architecture Decision Records)

**Plan de Acción**:
```markdown
# CHANGELOG.md
## [1.1.0] - 2026-04-20
### Added
- Tabla `payments_detail` en datamart
- Campo `payment_to_overdue` pre-calculado

### Changed
- Optimizadas queries en `clean_service.py` (-26% LOC)

### Fixed
- FK validation en pre-load
```

**Owner**: Todos los desarrolladores
**Estado**: 🟡 Mejorar prácticas

---

## 📈 Matriz de Riesgos

```
         │ Probabilidad
         │
  Alto   │              O1, O2
         │
         │
  Medio  │  T1, T2, T3, T4, D1, D2, D3, O3
         │
         │
  Bajo   │
         │
         └─────────────────────────────
           Bajo    Medio    Alto
                 Impacto
```

**Leyenda**:
- 🔴 Riesgo Crítico (requiere acción inmediata)
- 🟡 Riesgo Moderado (monitorear y mitigar)
- 🟢 Riesgo Bajo (bajo control)

---

## 🎯 Plan de Acción Priorizado

### 🔴 Urgente (0-30 días)

1. **[O1] Implementar Monitoreo y Alertas**
   - Owner: DevOps
   - Esfuerzo: 2 días
   - Impacto: Crítico

2. **[O2] Knowledge Transfer + Runbook**
   - Owner: Data Engineering Manager
   - Esfuerzo: 1 semana
   - Impacto: Crítico

3. **[T3] Configurar Alertas de Presupuesto GCP**
   - Owner: FinOps
   - Esfuerzo: 2 horas
   - Impacto: Alto

### 🟡 Importante (30-90 días)

4. **[T2] Schema Validation Pre-load**
   - Owner: Data Engineering
   - Esfuerzo: 3 días
   - Impacto: Medio

5. **[D1] Enmascaramiento PII en Rejects**
   - Owner: Data Governance
   - Esfuerzo: 1 semana
   - Impacto: Alto (compliance)

6. **[T1] Particionamiento si volumen crece**
   - Owner: Data Engineering
   - Esfuerzo: 1 semana
   - Condición: Si refresh >10 min

### 🟢 Mejoras (>90 días)

7. **[T4] Dependabot para actualizaciones**
   - Owner: DevOps
   - Esfuerzo: 1 día
   - Impacto: Bajo

8. **[O3] CHANGELOG + ADRs**
   - Owner: Todos
   - Esfuerzo: Continuo
   - Impacto: Bajo

---

## 📅 Calendario de Revisión

| Riesgo | Frecuencia Revisión | Próxima Revisión |
|--------|-------------------|------------------|
| O1, O2 (Críticos) | Mensual | Mayo 2026 |
| T1-T4, D1-D3, O3 (Moderados) | Trimestral | Julio 2026 |
| Todos | Anual | Abril 2027 |

---

## 📝 Historial de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-04-19 | 1.0 | Creación del registro de riesgos |

---
