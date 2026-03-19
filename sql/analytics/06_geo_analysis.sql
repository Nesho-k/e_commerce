-- =============================================================
-- ANALYTICS : Analyse géographique
-- Revenue et comportement par état brésilien
-- =============================================================

DROP TABLE IF EXISTS analytics.geo_analysis;

CREATE TABLE analytics.geo_analysis AS
SELECT
    c.state,

    COUNT(DISTINCT c.customer_unique_id)        AS unique_customers,
    COUNT(DISTINCT o.order_id)                  AS total_orders,
    SUM(p.total_payment)                        AS total_revenue,
    ROUND(AVG(p.total_payment)::numeric, 2)     AS avg_order_value,

    -- Délai moyen de livraison (les états éloignés attendent plus)
    ROUND(AVG(o.delivery_days)::numeric, 1)     AS avg_delivery_days,

    -- Taux de livraison dans les délais par état
    ROUND((AVG(o.delivered_on_time) * 100)::numeric, 2)    AS on_time_rate_pct,

    -- Note moyenne des clients de cet état
    ROUND(AVG(r.review_score)::numeric, 2)      AS avg_review_score,

    -- Revenue par client (intensité d'achat)
    ROUND((SUM(p.total_payment) / NULLIF(COUNT(DISTINCT c.customer_unique_id), 0))::numeric, 2) AS revenue_per_customer

FROM clean.customers c
JOIN clean.orders o    ON c.customer_id  = o.customer_id
JOIN clean.payments p  ON o.order_id     = p.order_id
LEFT JOIN clean.reviews r ON o.order_id  = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.state
ORDER BY total_revenue DESC;
