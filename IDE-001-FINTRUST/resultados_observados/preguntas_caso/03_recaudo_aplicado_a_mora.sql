-- =============================================
-- Query 3: Recaudo aplicado a cuotas en mora (por día)
-- =============================================
-- Descripción: 
--   Detalla los pagos aplicados a cuotas que ya estaban vencidas
--   Condiciones: payment_to_overdue = TRUE AND is_overdue = TRUE
--   Agrupado por día de pago
--   Usa 100% el datamart (view_payments_detail)
-- 
-- Uso:
--   Reemplazar {project_id} y {datamart_dataset} con tus valores reales

SELECT
  payment_date AS fecha_pago,
  COUNT(DISTINCT payment_id) AS total_pagos_a_mora,
  COUNT(DISTINCT installment_id) AS cuotas_en_mora_pagadas,
  COUNT(DISTINCT loan_id) AS creditos_con_pago_a_mora,
  
  -- Montos
  SUM(payment_amount) AS monto_total_pagado_a_mora,
  ROUND(AVG(payment_amount), 2) AS pago_promedio_a_mora,
  MIN(payment_amount) AS pago_minimo,
  MAX(payment_amount) AS pago_maximo,
  
  -- Días de atraso promedio al momento del pago
  ROUND(AVG(payment_days_after_due), 2) AS dias_atraso_promedio,
  MAX(payment_days_after_due) AS dias_atraso_maximo

FROM `{project_id}.{datamart_dataset}.view_payments_detail`

WHERE 
  -- Condición 1: El pago se realizó después de la fecha de vencimiento
  payment_to_overdue = TRUE
  -- Condición 2: La cuota está marcada como vencida (is_overdue = TRUE)
  AND is_overdue = TRUE

GROUP BY payment_date

ORDER BY payment_date DESC;
