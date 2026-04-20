CREATE OR REPLACE VIEW `{project_id}.{datamart_dataset}.view_loans_summary` AS

WITH loan_metrics AS (
  SELECT
    loan_id,
    
    -- Totales de cuotas
    COUNT(*) AS total_installments,
    SUM(installment_amount) AS total_loan_amount,
    
    -- Cuotas pagadas
    SUM(CASE WHEN is_paid THEN 1 ELSE 0 END) AS installments_paid,
    SUM(CASE WHEN is_paid THEN installment_amount ELSE 0 END) AS amount_fully_paid,
    
    -- Cuotas vencidas
    SUM(CASE WHEN is_overdue THEN 1 ELSE 0 END) AS installments_overdue,
    SUM(CASE WHEN is_overdue THEN outstanding_balance ELSE 0 END) AS overdue_balance,
    
    -- Cuotas al día (futuras o pagadas)
    SUM(CASE WHEN NOT is_overdue THEN 1 ELSE 0 END) AS installments_current,
    SUM(CASE WHEN NOT is_overdue AND NOT is_paid THEN outstanding_balance ELSE 0 END) AS current_balance,
    
    -- Pagos totales
    SUM(amount_paid) AS total_paid,
    
    -- Outstanding total
    SUM(outstanding_balance) AS total_outstanding,
    
    -- Mora máxima
    MAX(days_past_due) AS max_days_past_due,
    
    -- Última cuota vencida
    MAX(CASE WHEN is_overdue THEN due_date ELSE NULL END) AS last_overdue_date
    
  FROM `{project_id}.{datamart_dataset}.view_installments_master`
  GROUP BY loan_id
)

SELECT
  -- IDs
  l.loan_id,
  l.customer_id,
  
  -- Info Customer
  c.full_name AS customer_name,
  c.city,
  c.segment,
  c.monthly_income,
  
  -- Info Loan
  l.principal_amount,
  l.annual_rate,
  l.term_months,
  l.loan_status,
  l.product_type,
  l.origination_date,
  FORMAT_DATE('%Y-%m', l.origination_date) AS cohort,
  
  -- Métricas Agregadas
  lm.total_installments,
  lm.total_loan_amount,
  lm.installments_paid,
  lm.installments_overdue,
  lm.installments_current,
  
  -- Montos
  lm.amount_fully_paid,
  lm.total_paid,
  lm.total_outstanding,
  lm.overdue_balance,
  lm.current_balance,
  
  -- Mora
  lm.max_days_past_due,
  lm.last_overdue_date,
  
  -- Porcentajes
  ROUND(SAFE_DIVIDE(lm.installments_paid, lm.total_installments) * 100, 2) AS pct_installments_paid,
  ROUND(SAFE_DIVIDE(lm.total_paid, lm.total_loan_amount) * 100, 2) AS pct_amount_paid,
  ROUND(SAFE_DIVIDE(lm.overdue_balance, lm.total_loan_amount) * 100, 2) AS pct_overdue,
  
  -- Clasificación de Riesgo
  CASE
    WHEN lm.installments_overdue = 0 THEN 'Bajo Riesgo'
    WHEN lm.max_days_past_due <= 30 THEN 'Riesgo Moderado'
    WHEN lm.max_days_past_due <= 90 THEN 'Riesgo Alto'
    ELSE 'Riesgo Crítico'
  END AS risk_category

FROM `{project_id}.{clean_dataset}.loans` l
INNER JOIN `{project_id}.{clean_dataset}.customers` c 
  ON l.customer_id = c.customer_id
INNER JOIN loan_metrics lm 
  ON l.loan_id = lm.loan_id

ORDER BY l.customer_id, l.origination_date DESC;
