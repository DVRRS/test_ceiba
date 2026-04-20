-- =============================================
-- Query 5: Top 10 créditos con mayor mora
-- =============================================
-- Descripción: 
--   Lista los 10 créditos con mayor días de mora (max_days_past_due)
--   y mayor saldo vencido (overdue_balance)
--   A nivel de loan_id
-- 
-- Uso:
--   Reemplazar {project_id} y {datamart_dataset} con tus valores reales

SELECT
  loan_id,
  customer_id,
  customer_name,
  city,
  segment,
  
  -- Info del Crédito
  principal_amount AS monto_original,
  origination_date AS fecha_originacion,
  cohort AS cohorte,
  term_months AS plazo_meses,
  annual_rate AS tasa_anual,
  product_type AS tipo_producto,
  loan_status AS estado_credito,
  
  -- Métricas de Mora
  max_days_past_due AS dias_mora_maximos,
  last_overdue_date AS ultima_fecha_vencida,
  
  -- Saldos
  overdue_balance AS saldo_vencido,
  current_balance AS saldo_al_dia,
  total_outstanding AS saldo_total_pendiente,
  total_paid AS total_pagado,
  
  -- Cuotas
  total_installments AS total_cuotas,
  installments_paid AS cuotas_pagadas,
  installments_overdue AS cuotas_vencidas,
  installments_current AS cuotas_al_dia,
  
  -- Porcentajes
  pct_amount_paid AS pct_pagado,
  pct_overdue AS pct_vencido,
  
  -- Clasificación
  risk_category AS categoria_riesgo

FROM `{project_id}.{datamart_dataset}.view_loans_summary`

WHERE 
  -- Solo créditos con mora activa
  max_days_past_due > 0
  AND overdue_balance > 0

ORDER BY 
  max_days_past_due DESC,  -- Primero por días de mora
  overdue_balance DESC      -- Luego por saldo vencido

LIMIT 10;
