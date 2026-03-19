-- =============================================================
-- COUCHE CLEAN : customers
-- Nettoyage + infos géographiques
-- =============================================================

DROP TABLE IF EXISTS clean.customers;

CREATE TABLE clean.customers AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix AS zip_code,
    customer_city            AS city,
    customer_state           AS state
FROM raw.raw_customers
WHERE customer_id IS NOT NULL;
