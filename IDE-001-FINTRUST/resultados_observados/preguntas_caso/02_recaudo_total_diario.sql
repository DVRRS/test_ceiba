-- =============================================
-- Query 2: Recaudo total diario
-- =============================================
-- Descripción: 
--   Muestra el recaudo total por día (payment_amount),
--   separando cuánto fue aplicado a cuotas vencidas vs cuotas al día
--   Usa 100% el datamart (view_payments_detail)
-- 
-- Uso:
--   Reemplazar {project_id} y {datamart_dataset} con tus valores reales

SELECT
  payment_date AS fecha_pago,
  COUNT(*) AS total_pagos,
  SUM(payment_amount) AS recaudo_total,
  
  -- Recaudo aplicado a cuotas vencidas (en mora)
  SUM(CASE WHEN payment_to_overdue THEN payment_amount ELSE 0 END) AS recaudo_a_mora,
  COUNT(CASE WHEN payment_to_overdue THEN 1 ELSE NULL END) AS pagos_a_mora,
  
  -- Recaudo aplicado a cuotas al día
  SUM(CASE WHEN NOT payment_to_overdue THEN payment_amount ELSE 0 END) AS recaudo_al_dia,
  COUNT(CASE WHEN NOT payment_to_overdue THEN 1 ELSE NULL END) AS pagos_al_dia,
  
  -- Porcentajes
  ROUND(
    SAFE_DIVIDE(
      SUM(CASE WHEN payment_to_overdue THEN payment_amount ELSE 0 END),
      SUM(payment_amount)
    ) * 100, 
    2
  ) AS pct_recaudo_a_mora,
  
  ROUND(AVG(payment_amount), 2) AS pago_promedio

FROM `{project_id}.{datamart_dataset}.view_payments_detail`

GROUP BY payment_date

ORDER BY payment_date DESC;
