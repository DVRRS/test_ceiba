CREATE TABLE IF NOT EXISTS fintrust_raw_alpha.payments (
payment_id STRING,
loan_id STRING,
installment_id STRING,
payment_date DATE,
payment_amount NUMERIC,
payment_channel STRING,
payment_status STRING,
loaded_at TIMESTAMP
);
