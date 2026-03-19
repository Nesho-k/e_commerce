-- =============================================================
-- ANALYTICS : Top produits
-- Classement par revenus et volume de ventes
-- =============================================================

DROP TABLE IF EXISTS analytics.top_products;

CREATE TABLE analytics.top_products AS
SELECT
    oi.product_id,
    oi.category_english                     AS category,
    COUNT(DISTINCT oi.order_id)             AS total_orders,
    SUM(oi.price)                           AS total_revenue,
    ROUND(AVG(oi.price)::numeric, 2)        AS avg_price,
    ROUND(AVG(r.review_score)::numeric, 2)  AS avg_review_score,
    COUNT(DISTINCT oi.seller_id)            AS seller_count,

    -- Rang par revenu dans sa catégorie
    RANK() OVER (
        PARTITION BY oi.category_english
        ORDER BY SUM(oi.price) DESC
    ) AS rank_in_category

FROM clean.order_items oi
JOIN clean.orders o  ON oi.order_id  = o.order_id
LEFT JOIN clean.reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY oi.product_id, oi.category_english
ORDER BY total_revenue DESC;


-- Top catégories (agrégé)
DROP TABLE IF EXISTS analytics.top_categories;

CREATE TABLE analytics.top_categories AS
SELECT
    category_english                        AS category,
    COUNT(DISTINCT order_id)                AS total_orders,
    SUM(price)                              AS total_revenue,
    ROUND(AVG(price)::numeric, 2)           AS avg_price,
    COUNT(DISTINCT product_id)              AS unique_products
FROM clean.order_items
GROUP BY category_english
ORDER BY total_revenue DESC;
