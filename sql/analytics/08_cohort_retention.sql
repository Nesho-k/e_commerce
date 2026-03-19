-- =============================================================
-- ANALYTICS : Cohorte et rétention clients
-- Chaque cohorte = mois du premier achat d'un client
-- On mesure combien reviennent les mois suivants
-- =============================================================

DROP TABLE IF EXISTS analytics.cohort_retention;

CREATE TABLE analytics.cohort_retention AS
WITH first_order AS (
    -- Mois de la première commande de chaque client unique
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', MIN(o.purchased_at)) AS cohort_month
    FROM clean.customers c
    JOIN clean.orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_activity AS (
    -- Tous les mois d'activité de chaque client
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', o.purchased_at) AS activity_month
    FROM clean.customers c
    JOIN clean.orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, DATE_TRUNC('month', o.purchased_at)
)
SELECT
    f.cohort_month,
    -- Mois 0 = premier achat, Mois 1 = 1 mois après, etc.
    EXTRACT(YEAR FROM AGE(a.activity_month, f.cohort_month)) * 12
    + EXTRACT(MONTH FROM AGE(a.activity_month, f.cohort_month)) AS months_since_first_order,

    COUNT(DISTINCT a.customer_unique_id)    AS active_customers

FROM first_order f
JOIN customer_activity a ON f.customer_unique_id = a.customer_unique_id
GROUP BY f.cohort_month, months_since_first_order
ORDER BY cohort_month, months_since_first_order;
