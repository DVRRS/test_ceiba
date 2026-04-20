CREATE TABLE IF NOT EXISTS fintrust_raw_alpha.loans (
loan_id STRING,
customer_id STRING,
origination_date DATE,
principal_amount NUMERIC,
annual_rate NUMERIC,
term_months INT64,
loan_status STRING,
product_type STRING
);
