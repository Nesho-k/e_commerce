-- =============================================================
-- ANALYTICS : Customer Lifetime Value (CLV)
-- Valeur totale générée par chaque client unique
-- =============================================================

DROP TABLE IF EXISTS analytics.customer_lifetime_value;

CREATE TABLE analytics.customer_lifetime_value AS
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        c.state,
        c.city,
        COUNT(DISTINCT o.order_id)              AS total_orders,
        SUM(p.total_payment)                    AS total_spent,
        MIN(o.purchased_at)                     AS first_order_date,
        MAX(o.purchased_at)                     AS last_order_date,
        ROUND(AVG(p.total_payment)::numeric, 2) AS avg_order_value,

        -- Durée de vie client en jours
        EXTRACT(DAY FROM (MAX(o.purchased_at) - MIN(o.purchased_at))) AS customer_lifespan_days

    FROM clean.customers c
    JOIN clean.orders o   ON c.customer_id     = o.customer_id
    JOIN clean.payments p ON o.order_id        = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, c.state, c.city
)
SELECT
    *,
    -- Segmentation client
    CASE
        WHEN total_spent >= 500  THEN 'high_value'
        WHEN total_spent >= 200  THEN 'mid_value'
        ELSE                          'low_value'
    END AS customer_segment,

    -- Client fidèle = plus d'une commande
    CASE WHEN total_orders > 1 THEN 1 ELSE 0 END AS is_repeat_customer

FROM customer_orders
ORDER BY total_spent DESC;
