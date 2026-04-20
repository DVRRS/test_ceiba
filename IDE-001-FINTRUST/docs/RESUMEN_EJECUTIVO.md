# Resumen Ejecutivo - Pipeline FinTrust

**Proyecto**: Data Quality & Datamart  
**Fecha**: Abril 19, 2026  
**Estado**: ✅ Producción

---

## 🎯 Objetivo

Pipeline automatizado para limpieza, validación y construcción de datamart analítico de cartera de créditos FinTrust.

---

## 📊 Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Raw Dataset │  →   │ Clean       │  →   │  Datamart   │
│ (Origen)    │      │ (Validado)  │      │ (Analítica) │
└─────────────┘      └─────────────┘      └─────────────┘
                            ↓
                     ┌─────────────┐
                     │  Rejects    │
                     │ (Rechazos)  │
                     └─────────────┘
```

**Stack**: FastAPI + BigQuery + Python 3.11

---

## ✅ Decisiones Técnicas Clave

| Decisión | Razón | Trade-off |
|----------|-------|-----------|
| **3 Capas (Raw/Clean/Datamart)** | Auditoría y flexibilidad | +30% storage |
| **MERGE Incremental** | Eficiencia y idempotencia | Complejidad SQL |
| **Pre-load Gating** | Calidad garantizada | Storage de rejects |
| **Tablas + Vistas** | Performance vs Freshness | Duplicación SQL |
| **CREATE OR REPLACE** | Atomicidad | No incremental |

---

## 🤔 Supuestos Críticos

### ✅ Supuestos Validados (Confirmados)

| Supuesto | Status |
|----------|--------|
| Volumen diario < 1M registros | ✅ Confirmado |
| Refresh diario es suficiente | ✅ Confirmado |
| PK única en raw (o deduplicable) | ✅ Manejado por código |

### ⚠️ Supuestos a Confirmar con Negocio

| Supuesto | Código Actual | Pregunta Clave |
|----------|---------------|----------------|
| **Watermark = última versión** | Si hay duplicados del mismo PK, se elige el registro con mayor `created_at/loaded_at` | ¿La fecha más reciente siempre representa la versión correcta? |
| **Tasas >200% = error** | DQ check marca como violation si `annual_rate > 200` | ¿Existen créditos legítimos con tasas >200%? |
| **Parent antes que Child** | Si un `loan` llega sin `customer`, se rechaza | ¿Los datos siempre llegan en orden (customers → loans → installments → payments)? |

---

## ⚠️ Top 5 Riesgos

**📋 Ver registro completo**: [`RIESGOS.md`](./RIESGOS.md)

| # | Riesgo | Probabilidad | Mitigación |
|---|--------|--------------|------------|
| 1 | **Falta de monitoreo** | 🔴 Alta | Cloud Monitoring + alertas |
| 2 | **Costos de BigQuery** | 🟡 Media | Particionamiento + presupuesto |
| 3 | **Schema drift en Raw** | 🟡 Media | Schema validation pre-load |
| 4 | **Performance (>50M registros)** | 🟡 Media | MERGE incremental en datamart |
| 5 | **Datos sensibles en Rejects** | 🟡 Media | Enmascaramiento PII + TTL 90d |

**10 riesgos totales**: 2 críticos 🔴 | 8 moderados 🟡

---

## 📈 Calidad de Datos

**Validaciones Implementadas**: 18 checks automáticos

- ✅ PK: Not null + unique (4 tablas)
- ✅ FK: Referential integrity (3 relaciones)
- ✅ Business rules: Montos, fechas, tasas (8 reglas)
- ✅ Complex: Payments vs installments (1 regla)

**Evidencia**:
- 53 tests unitarios (100% passing)
- Documento formal de validación (`EVIDENCIA_CALIDAD_DATOS.md`)
- Tablas de rejects con `_reason_` column

---

## 🎯 Datamart

**6 Objetos** (3 tablas + 3 vistas):

| Nivel | Propósito | Performance | Freshness |
|-------|-----------|-------------|-----------|
| **Installments Master** | Detalle por cuota | ⚡⚡⚡ (tabla) | ✅✅✅ (vista) |
| **Loans Summary** | Agregado por crédito | ⚡⚡⚡ (tabla) | ✅✅✅ (vista) |
| **Payments Detail** | Pagos individuales | ⚡⚡⚡ (tabla) | ✅✅✅ (vista) |

**100% Autocontenido**: Todas las queries analíticas usan solo el datamart.

---

## 🔄 Próximos Pasos (Priorizados)

### 🔴 Crítico (0-30 días)
1. Implementar Cloud Monitoring + alertas
2. Configurar presupuesto GCP
3. Knowledge transfer al equipo

### 🟡 Importante (30-90 días)
4. Schema validation pre-load
5. Enmascaramiento PII en rejects
6. Particionamiento si volumen crece

### 🟢 Nice-to-have (>90 días)
7. Dependabot para actualizaciones
8. Dashboard de salud del pipeline
9. Optimización incremental en datamart

---

## 📊 Métricas Clave

| Métrica | Valor Actual | Objetivo | Estado |
|---------|--------------|----------|--------|
| Tests pasados | 53/53 | 100% | ✅ |
| Cobertura DQ | 18 checks | 100% reglas | ✅ |
| Queries datamart | 5/5 | 100% datamart | ✅ |

---

## 💰 Consideraciones de Costo (USD)

**BigQuery**:
- Storage: ~$0.02/GB/mes (Raw + Clean + Datamart)
- Queries: ~$5/TB escaneado (on-demand)
- **Optimización**: Tablas materializadas evitan re-scans

**Cloud Run**:
- $0.00002400/vCPU-seg + $0.00000250/GiB-seg
- **Estimado**: <$20/mes con <1000 requests/día

**Total estimado**: $50-100/mes (varía con volumen)

---

## 📞 Contacto

**Owner**: Bryan David Rosas
**Equipo**: Data Engineering  
**Documentación**: `/python/README.md`
**Repositorio**: `test_ceiba/IDE-001-FINTRUST/resultados_observados/python/`

---

**Última actualización**: Abril 19, 2026
