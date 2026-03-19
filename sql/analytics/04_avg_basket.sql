-- =============================================================
-- ANALYTICS : Panier moyen + performance livraison
-- Vue globale des KPI opérationnels
-- =============================================================

DROP TABLE IF EXISTS analytics.kpi_summary;

CREATE TABLE analytics.kpi_summary AS
SELECT
    DATE_TRUNC('month', o.purchased_at)         AS month,

    -- Panier moyen
    ROUND(AVG(p.total_payment)::numeric, 2)     AS avg_basket,

    -- Nombre de commandes
    COUNT(DISTINCT o.order_id)                  AS total_orders,

    -- Taux de livraison dans les délais
    ROUND((AVG(o.delivered_on_time) * 100)::numeric, 2)    AS on_time_delivery_rate_pct,

    -- Délai moyen de livraison
    ROUND(AVG(o.delivery_days)::numeric, 1)     AS avg_delivery_days,

    -- Note moyenne des avis
    ROUND(AVG(r.review_score)::numeric, 2)      AS avg_review_score,

    -- Taux de commandes avec avis
    ROUND((AVG(r.has_comment) * 100)::numeric, 2)          AS review_comment_rate_pct,

    -- Taux d'annulation du mois
    ROUND(
        COUNT(CASE WHEN o.order_status = 'canceled' THEN 1 END)::numeric
        / NULLIF(COUNT(*), 0) * 100
    , 2) AS cancellation_rate_pct

FROM clean.orders o
JOIN  clean.payments p ON o.order_id = p.order_id
LEFT JOIN clean.reviews r  ON o.order_id = r.order_id
GROUP BY DATE_TRUNC('month', o.purchased_at)
ORDER BY month;
