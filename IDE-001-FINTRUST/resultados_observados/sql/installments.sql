CREATE TABLE IF NOT EXISTS fintrust_raw_alpha.installments (
installment_id STRING,
loan_id STRING,
installment_number INT64,
due_date DATE,
principal_due NUMERIC,
interest_due NUMERIC,
installment_status STRING
);
