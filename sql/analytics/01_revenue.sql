-- =============================================================
-- ANALYTICS : Chiffre d'affaires
-- Granularité : journalière et mensuelle
-- =============================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- Revenue journalier
DROP TABLE IF EXISTS analytics.daily_revenue;

CREATE TABLE analytics.daily_revenue AS
SELECT
    DATE(o.purchased_at)            AS order_date,
    COUNT(DISTINCT o.order_id)      AS total_orders,
    SUM(p.total_payment)            AS revenue,
    ROUND(AVG(p.total_payment)::numeric, 2) AS avg_order_value
FROM clean.orders o
JOIN clean.payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY DATE(o.purchased_at)
ORDER BY order_date;


-- Revenue mensuel
DROP TABLE IF EXISTS analytics.monthly_revenue;

CREATE TABLE analytics.monthly_revenue AS
WITH monthly_base AS (
    SELECT
        DATE_TRUNC('month', o.purchased_at) AS month,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        SUM(p.total_payment)                AS revenue,
        ROUND(AVG(p.total_payment)::numeric, 2) AS avg_order_value
    FROM clean.orders o
    JOIN clean.payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY DATE_TRUNC('month', o.purchased_at)
    -- Exclut les mois avec moins de 100 commandes (début dataset non représentatif)
    HAVING COUNT(DISTINCT o.order_id) >= 100
)
SELECT
    month,
    total_orders,
    revenue,
    avg_order_value,

    -- Croissance vs mois précédent (%) — calculée sur données filtrées uniquement
    ROUND(
        (revenue::numeric - LAG(revenue::numeric) OVER (ORDER BY month))
        / NULLIF(LAG(revenue::numeric) OVER (ORDER BY month), 0) * 100
    , 2) AS revenue_growth_pct

FROM monthly_base
ORDER BY month;
