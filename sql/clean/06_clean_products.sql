-- =============================================================
-- COUCHE CLEAN : products
-- Nettoyage du catalogue produits
-- =============================================================

DROP TABLE IF EXISTS clean.products;

CREATE TABLE clean.products AS
SELECT
    p.product_id,

    -- Traduction catégorie en anglais
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    p.product_category_name                     AS category_pt,

    -- Dimensions physiques (utiles pour frais de port)
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,

    -- Volume en cm³ (indicateur de taille du colis)
    CASE
        WHEN p.product_length_cm IS NOT NULL
         AND p.product_height_cm IS NOT NULL
         AND p.product_width_cm  IS NOT NULL
        THEN p.product_length_cm * p.product_height_cm * p.product_width_cm
        ELSE NULL
    END AS volume_cm3,

    -- Nombre de photos (signal de qualité du listing)
    COALESCE(p.product_photos_qty, 0)           AS photos_count

FROM raw.raw_products p
LEFT JOIN raw.raw_product_category_translation t
       ON p.product_category_name = t.product_category_name
WHERE p.product_id IS NOT NULL;
