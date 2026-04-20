CREATE OR REPLACE TABLE `{project_id}.{datamart_dataset}.table_installments_master` AS

WITH payments_agg AS (
  -- Agregamos pagos por installment_id
  SELECT
    installment_id,
    SUM(payment_amount) AS amount_paid,
    COUNT(*) AS payment_count,
    MAX(payment_date) AS last_payment_date
  FROM `{project_id}.{clean_dataset}.payments`
  GROUP BY installment_id
)

SELECT
  -- IDs y Llaves
  i.installment_id,
  i.loan_id,
  l.customer_id,
  
  -- Información del Customer
  c.full_name AS customer_name,
  c.city,
  c.segment,
  c.monthly_income,
  
  -- Información del Loan
  l.principal_amount AS loan_principal,
  l.annual_rate,
  l.term_months,
  l.loan_status,
  l.product_type,
  l.origination_date,
  FORMAT_DATE('%Y-%m', l.origination_date) AS cohort,  -- Cohort calculado (YYYY-MM)
  
  -- Información del Installment
  i.installment_number,
  i.due_date,
  i.principal_due,
  i.interest_due,
  (i.principal_due + i.interest_due) AS installment_amount,  -- Monto total de la cuota
  i.installment_status,
  
  -- Métricas de Pago
  COALESCE(pa.amount_paid, 0) AS amount_paid,  -- Total pagado en esta cuota
  COALESCE(pa.payment_count, 0) AS payment_count,  -- Número de pagos realizados
  pa.last_payment_date,  -- Fecha del último pago
  
  -- Outstanding Balance (Saldo Pendiente)
  (i.principal_due + i.interest_due) - COALESCE(pa.amount_paid, 0) AS outstanding_balance,
  
  -- Is Overdue (boolean)
  CASE
    WHEN i.due_date < CURRENT_DATE() 
         AND ((i.principal_due + i.interest_due) - COALESCE(pa.amount_paid, 0)) > 0.01  -- Tolerancia de 1 centavo
    THEN TRUE
    ELSE FALSE
  END AS is_overdue,
  
  -- Days Past Due (días de mora)
  CASE
    WHEN i.due_date < CURRENT_DATE() 
         AND ((i.principal_due + i.interest_due) - COALESCE(pa.amount_paid, 0)) > 0.01
    THEN DATE_DIFF(CURRENT_DATE(), i.due_date, DAY)
    ELSE 0
  END AS days_past_due,
  
  -- Flags Adicionales
  CASE
    WHEN COALESCE(pa.amount_paid, 0) >= (i.principal_due + i.interest_due)
    THEN TRUE
    ELSE FALSE
  END AS is_paid,  -- Si la cuota está completamente pagada
  
  CASE
    WHEN i.due_date > CURRENT_DATE()
    THEN TRUE
    ELSE FALSE
  END AS is_future,  -- Si la cuota aún no vence
  
  -- Clasificación de Mora
  CASE
    WHEN i.due_date >= CURRENT_DATE() THEN 'Al día'
    WHEN ((i.principal_due + i.interest_due) - COALESCE(pa.amount_paid, 0)) <= 0.01 THEN 'Pagada'
    WHEN DATE_DIFF(CURRENT_DATE(), i.due_date, DAY) <= 30 THEN 'Mora 1-30 días'
    WHEN DATE_DIFF(CURRENT_DATE(), i.due_date, DAY) <= 60 THEN 'Mora 31-60 días'
    WHEN DATE_DIFF(CURRENT_DATE(), i.due_date, DAY) <= 90 THEN 'Mora 61-90 días'
    ELSE 'Mora >90 días'
  END AS mora_bucket,
  
  -- Timestamp de actualización
  CURRENT_TIMESTAMP() AS _updated_at

FROM `{project_id}.{clean_dataset}.installments` i
INNER JOIN `{project_id}.{clean_dataset}.loans` l 
  ON i.loan_id = l.loan_id
INNER JOIN `{project_id}.{clean_dataset}.customers` c 
  ON l.customer_id = c.customer_id
LEFT JOIN payments_agg pa 
  ON i.installment_id = pa.installment_id

ORDER BY l.customer_id, i.loan_id, i.installment_number;
