-- =============================================================
-- ANALYTICS : Analyse des modes de paiement
-- =============================================================

DROP TABLE IF EXISTS analytics.payment_analysis;

CREATE TABLE analytics.payment_analysis AS
SELECT
    DATE_TRUNC('month', o.purchased_at)         AS month,
    p.payment_types,

    COUNT(DISTINCT o.order_id)                  AS total_orders,
    SUM(p.total_payment)                        AS total_revenue,
    ROUND(AVG(p.total_payment)::numeric, 2)     AS avg_payment,
    ROUND(AVG(p.payment_installments_count)::numeric, 1) AS avg_installments

FROM clean.orders o
JOIN clean.payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY DATE_TRUNC('month', o.purchased_at), p.payment_types
ORDER BY month, total_revenue DESC;
