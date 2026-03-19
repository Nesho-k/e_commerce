-- =============================================================
-- ANALYTICS : Performance des vendeurs
-- =============================================================

DROP TABLE IF EXISTS analytics.seller_performance;

CREATE TABLE analytics.seller_performance AS
SELECT
    oi.seller_id,
    s.city                                      AS seller_city,
    s.state                                     AS seller_state,

    COUNT(DISTINCT oi.order_id)                 AS total_orders,
    SUM(oi.price)                               AS total_revenue,
    ROUND(AVG(oi.price)::numeric, 2)            AS avg_product_price,
    COUNT(DISTINCT oi.product_id)               AS unique_products,

    -- Qualité : note moyenne des avis
    ROUND(AVG(r.review_score)::numeric, 2)      AS avg_review_score,

    -- Délai moyen de livraison
    ROUND(AVG(o.delivery_days)::numeric, 1)     AS avg_delivery_days,

    -- Taux de livraison dans les délais
    ROUND((AVG(o.delivered_on_time) * 100)::numeric, 2)    AS on_time_rate_pct,

    -- Classement global par revenue
    RANK() OVER (ORDER BY SUM(oi.price) DESC)   AS revenue_rank

FROM clean.order_items oi
JOIN clean.orders o    ON oi.order_id  = o.order_id
JOIN clean.sellers s   ON oi.seller_id = s.seller_id
LEFT JOIN clean.reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY oi.seller_id, s.city, s.state
ORDER BY total_revenue DESC;
