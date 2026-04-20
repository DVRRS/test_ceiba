-- =============================================
-- Query 4: Cartera (saldo) por cohorte
-- =============================================
-- Descripción: 
--   Muestra el saldo pendiente total (outstanding_balance) agrupado por cohorte
--   Incluye saldo vencido (overdue_balance) y saldo al día (current_balance)
--   Cohorte = año-mes de originación (FORMAT_DATE('%Y-%m', origination_date))
-- 
-- Uso:
--   Reemplazar {project_id} y {datamart_dataset} con tus valores reales

SELECT
  cohort AS cohorte,
  COUNT(DISTINCT loan_id) AS total_creditos,
  COUNT(DISTINCT customer_id) AS total_clientes,
  
  -- Montos Originados
  SUM(principal_amount) AS monto_originado_total,
  ROUND(AVG(principal_amount), 2) AS monto_originado_promedio,
  
  -- Saldo Total (Pendiente)
  SUM(total_outstanding) AS saldo_pendiente_total,
  
  -- Saldo Vencido (En Mora)
  SUM(overdue_balance) AS saldo_vencido_total,
  
  -- Saldo Al Día (Futuro)
  SUM(current_balance) AS saldo_al_dia_total,
  
  -- Total Pagado
  SUM(total_paid) AS total_pagado,
  
  -- Porcentajes
  ROUND(
    SAFE_DIVIDE(SUM(total_paid), SUM(principal_amount)) * 100, 
    2
  ) AS pct_pagado,
  
  ROUND(
    SAFE_DIVIDE(SUM(overdue_balance), SUM(total_outstanding)) * 100, 
    2
  ) AS pct_saldo_vencido,
  
  ROUND(
    SAFE_DIVIDE(SUM(current_balance), SUM(total_outstanding)) * 100, 
    2
  ) AS pct_saldo_al_dia,
  
  -- Métricas de Riesgo
  SUM(CASE WHEN risk_category = 'Riesgo Crítico' THEN 1 ELSE 0 END) AS creditos_criticos,
  SUM(CASE WHEN risk_category = 'Riesgo Alto' THEN 1 ELSE 0 END) AS creditos_alto_riesgo,
  SUM(CASE WHEN risk_category = 'Riesgo Moderado' THEN 1 ELSE 0 END) AS creditos_riesgo_moderado,
  SUM(CASE WHEN risk_category = 'Bajo Riesgo' THEN 1 ELSE 0 END) AS creditos_bajo_riesgo

FROM `{project_id}.{datamart_dataset}.view_loans_summary`

GROUP BY cohort

ORDER BY cohort DESC;
