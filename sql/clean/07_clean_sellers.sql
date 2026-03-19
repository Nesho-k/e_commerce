-- =============================================================
-- COUCHE CLEAN : sellers
-- Nettoyage des vendeurs
-- =============================================================

DROP TABLE IF EXISTS clean.sellers;

CREATE TABLE clean.sellers AS
SELECT
    seller_id,
    seller_zip_code_prefix  AS zip_code,
    seller_city             AS city,
    seller_state            AS state
FROM raw.raw_sellers
WHERE seller_id IS NOT NULL;
