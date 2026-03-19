-- =============================================================
-- COUCHE CLEAN : order_items
-- Jointure produits + traduction catégorie en anglais
-- =============================================================

DROP TABLE IF EXISTS clean.order_items;

CREATE TABLE clean.order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value AS total_item_value,

    -- Infos produit
    p.product_category_name,
    COALESCE(t.product_category_name_english, p.product_category_name) AS category_english,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm

FROM raw.raw_order_items oi
LEFT JOIN raw.raw_products p
       ON oi.product_id = p.product_id
LEFT JOIN raw.raw_product_category_translation t
       ON p.product_category_name = t.product_category_name
WHERE oi.order_id IS NOT NULL
  AND oi.price > 0;
