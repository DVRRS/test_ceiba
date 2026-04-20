-- =============================================
-- Query 1: Desembolso por día, ciudad y segmento
-- =============================================
-- Descripción: 
--   Muestra el monto total desembolsado (principal_amount) 
--   agrupado por fecha de originación, ciudad y segmento del cliente
--   Usa view_loans_summary del datamart como fuente única
-- 
-- Uso:
--   Reemplazar {project_id} y {datamart_dataset} con tus valores reales

SELECT
  origination_date AS fecha_desembolso,
  city AS ciudad,
  segment AS segmento,
  COUNT(DISTINCT loan_id) AS total_creditos,
  SUM(principal_amount) AS total_desembolsado,
  ROUND(AVG(principal_amount), 2) AS desembolso_promedio,
  MIN(principal_amount) AS desembolso_minimo,
  MAX(principal_amount) AS desembolso_maximo

FROM `{project_id}.{datamart_dataset}.view_loans_summary`

GROUP BY 
  origination_date,
  city,
  segment

ORDER BY 
  origination_date DESC,
  total_desembolsado DESC;
