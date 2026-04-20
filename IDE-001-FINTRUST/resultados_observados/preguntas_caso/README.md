# Queries de Análisis - Preguntas del Caso

Este directorio contiene queries SQL para responder preguntas clave del negocio basadas en el datamart de FinTrust.

## 📋 Índice de Queries

| # | Archivo | Descripción | Vista Principal |
|---|---------|-------------|-----------------|
| 1 | `01_desembolso_por_dia_ciudad_segmento.sql` | Desembolso por día, ciudad y segmento | `view_loans_summary` ✅ |
| 2 | `02_recaudo_total_diario.sql` | Recaudo total diario (con separación mora vs al día) | `view_payments_detail` ✅ |
| 3 | `03_recaudo_aplicado_a_mora.sql` | Recaudo aplicado específicamente a cuotas en mora | `view_payments_detail` ✅ |
| 4 | `04_cartera_saldo_por_cohorte.sql` | Saldo pendiente por cohorte de originación | `view_loans_summary` ✅ |
| 5 | `05_top10_creditos_mayor_mora.sql` | Top 10 créditos con mayor mora | `view_loans_summary` ✅ |

**✅ TODAS las queries usan 100% el datamart - No acceden a tablas `clean` directamente**

---

## 🔧 Uso


### Ejecutar en BigQuery

1. Abre [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Selecciona tu proyecto
3. Copia el contenido de la query
4. Reemplaza los placeholders, según el proyecto y los datasets (la idea es que sea replicable y escalable)
5. Ejecuta la query

**Filtros**:
- Solo créditos con mora activa (`max_days_past_due > 0`)
- Solo créditos con saldo vencido (`overdue_balance > 0`)

**Información incluida**:
- Identificación del cliente
- Métricas del crédito original
- Estado actual de mora
- Saldos (vencido, al día, total)
- Clasificación de riesgo

**Caso de uso**: 
- Priorización de gestión de cobranza
- Análisis de casos críticos
- Reportes de cartera de alto riesgo
- Planificación de provisiones

---

## 📈 Casos de Uso por Rol

### Analista de Riesgo
- Query 4: Cartera por cohorte (análisis)
- Query 5: Top 10 mora (seguimiento de casos críticos)

### Gerente de Cobranza
- Query 2: Recaudo diario (monitoreo de gestión)
- Query 3: Recaudo a mora (efectividad de cobranza)
- Query 5: Top 10 mora (priorización)

### Gerente Comercial
- Query 1: Desembolso por ciudad/segmento (planeación comercial)
- Query 4: Cartera por cohorte (evaluación de producto)

### CFO / Finanzas
- Query 2: Recaudo diario (flujo de caja)
- Query 4: Cartera por cohorte (provisiones)

### BI / Reporting
- Todas las queries pueden ser usadas como base para dashboards en Looker/Tableau/Power BI

---

## 🔗 Dependencias

**✅ TODAS las queries usan 100% el datamart** - No acceden a tablas `dataset_clean` directamente.

**Recomendación**: 
- Para reportes frecuentes: Usa las **TABLAS** (más rápidas, refrescar diariamente)
- Para datos en tiempo real: Usa las **VISTAS** (siempre actualizadas)

**Ventajas del diseño**:
- Single Source of Truth completo
- Consistencia garantizada en reglas de negocio
- No necesitas permisos en `dataset_clean` para consultas analíticas
- Toda la lógica de mora, saldos y clasificaciones está centralizada

---

## 📝 Notas Técnicas

### Arquitectura de Datos
**Principio**: Todas las queries usan 100% el datamart como fuente única de verdad.

- **Queries 1, 4, 5**: Usan `view_loans_summary` (datamart)
- **Queries 2, 3**: Usan `view_payments_detail` (datamart)

### Performance
- Las queries están optimizadas para usar las vistas del datamart
- Se evitan joins complejos innecesarios
- Se usan agregaciones eficientes

### Precisión
- Los cálculos de mora consideran `CURRENT_DATE()`
- Los saldos incluyen tolerancia de 1 centavo para redondeos
- Los porcentajes usan `SAFE_DIVIDE` para evitar división por cero

### Compatibilidad
- Todas las queries están escritas en **SQL estándar de BigQuery**
- Compatible con BigQuery versión 2.0+
- No requieren funciones UDF personalizadas

---

**Última actualización**: Abril 19, 2026  
**Autor**: Bryan David Rosas
**Versión**: 1.0
