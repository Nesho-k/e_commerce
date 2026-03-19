-- =============================================================
-- COUCHE CLEAN : payments
-- Agrégation des paiements par commande (une commande peut avoir
-- plusieurs paiements : ex. carte + bon cadeau)
-- =============================================================

DROP TABLE IF EXISTS clean.payments;

CREATE TABLE clean.payments AS
SELECT
    order_id,
    COUNT(*)                          AS payment_installments_count,
    SUM(payment_value)                AS total_payment,
    -- Modes de paiement utilisés (peut en avoir plusieurs)
    STRING_AGG(DISTINCT payment_type, ', ' ORDER BY payment_type) AS payment_types
FROM raw.raw_order_payments
WHERE order_id IS NOT NULL
  AND payment_value > 0
GROUP BY order_id;
