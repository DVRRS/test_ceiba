CREATE OR REPLACE VIEW `{project_id}.{datamart_dataset}.view_payments_detail` AS

-- =============================================
-- Vista: Detalle de Pagos (Payments Detail)
-- =============================================
-- Propósito:
--   Proporcionar información completa de cada pago individual,
--   enriquecido con el contexto del installment, loan y customer.
--   Permite análisis diarios de recaudo sin necesidad de acceder
--   a las tablas clean directamente.
--
-- Casos de uso:
--   - Análisis de recaudo diario
--   - Seguimiento de pagos a cuotas en mora
--   - Análisis de comportamiento de pago por cliente/segmento
--   - Análisis de canales de pago

SELECT
  -- Información del Pago
  p.payment_id,
  p.payment_date,
  p.payment_amount,
  p.payment_channel,
  p.payment_status,
  p.loaded_at AS payment_loaded_at,
  
  -- IDs de Relación
  p.loan_id,
  p.installment_id,
  im.customer_id,
  
  -- Información del Installment (desde view_installments_master)
  im.installment_number,
  im.due_date,
  im.installment_amount,
  im.principal_due,
  im.interest_due,
  im.installment_status,
  
  -- Métricas del Installment
  im.amount_paid AS installment_amount_paid_total,  -- Total pagado en esta cuota (incluyendo este pago)
  im.payment_count AS installment_payment_count,
  im.outstanding_balance AS installment_outstanding_balance,
  im.is_overdue,
  im.days_past_due,
  im.is_paid AS installment_is_paid,
  im.is_future AS installment_is_future,
  im.mora_bucket,
  
  -- Información del Cliente
  im.customer_name,
  im.city,
  im.segment,
  im.monthly_income,
  
  -- Información del Loan
  im.loan_principal,
  im.annual_rate,
  im.term_months,
  im.loan_status,
  im.product_type,
  im.origination_date,
  im.cohort,
  
  -- Flags Calculados para el Pago
  CASE
    WHEN p.payment_date > im.due_date THEN TRUE
    ELSE FALSE
  END AS payment_to_overdue,  -- Si el pago fue aplicado a una cuota ya vencida
  
  CASE
    WHEN p.payment_date > im.due_date THEN DATE_DIFF(p.payment_date, im.due_date, DAY)
    ELSE 0
  END AS payment_days_after_due,  -- Días de atraso al momento del pago
  
  CASE
    WHEN p.payment_date <= im.due_date THEN TRUE
    ELSE FALSE
  END AS payment_on_time  -- Si el pago se hizo antes o en la fecha de vencimiento

FROM `{project_id}.{clean_dataset}.payments` p
INNER JOIN `{project_id}.{datamart_dataset}.view_installments_master` im
  ON p.installment_id = im.installment_id

ORDER BY p.payment_date DESC, p.payment_id;
