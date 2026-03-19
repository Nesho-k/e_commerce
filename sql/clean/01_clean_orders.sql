-- =============================================================
-- COUCHE CLEAN : orders
-- Nettoyage des commandes + calcul statut livraison
-- =============================================================

CREATE SCHEMA IF NOT EXISTS clean;

DROP TABLE IF EXISTS clean.orders;

CREATE TABLE clean.orders AS
SELECT
    order_id,
    customer_id,
    order_status,

    -- Conversion des colonnes dates (stockées en texte dans le raw)
    order_purchase_timestamp::timestamp      AS purchased_at,
    order_approved_at::timestamp             AS approved_at,
    order_delivered_carrier_date::timestamp  AS shipped_at,
    order_delivered_customer_date::timestamp AS delivered_at,
    order_estimated_delivery_date::timestamp AS estimated_delivery_at,

    -- KPI : livraison dans les délais (1 = oui, 0 = non)
    CASE
        WHEN order_delivered_customer_date IS NOT NULL
         AND order_estimated_delivery_date IS NOT NULL
         AND order_delivered_customer_date::timestamp <= order_estimated_delivery_date::timestamp
        THEN 1 ELSE 0
    END AS delivered_on_time,

    -- KPI : délai de livraison en jours
    CASE
        WHEN order_delivered_customer_date IS NOT NULL
         AND order_purchase_timestamp IS NOT NULL
        THEN EXTRACT(DAY FROM (
            order_delivered_customer_date::timestamp - order_purchase_timestamp::timestamp
        ))
        ELSE NULL
    END AS delivery_days

FROM raw.raw_orders
WHERE order_id IS NOT NULL;
-- NOTE : on garde TOUTES les commandes (y compris annulées et unavailable)
-- Le filtre sur order_status se fait dans la couche analytics selon le besoin :
--   → KPI revenue : WHERE order_status = 'delivered'
--   → KPI taux annulation : WHERE order_status = 'canceled'
