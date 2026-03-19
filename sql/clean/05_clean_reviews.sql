-- =============================================================
-- COUCHE CLEAN : reviews
-- Nettoyage des avis clients
-- =============================================================

DROP TABLE IF EXISTS clean.reviews;

CREATE TABLE clean.reviews AS
SELECT
    review_id,
    order_id,
    review_score,                               -- Note de 1 à 5

    -- Nettoyage du titre (certains sont NULL)
    COALESCE(review_comment_title, '')          AS review_title,

    -- Nettoyage du commentaire (beaucoup sont NULL)
    COALESCE(review_comment_message, '')        AS review_message,

    -- Indicateur : l'avis a-t-il un commentaire écrit ?
    CASE
        WHEN review_comment_message IS NOT NULL
         AND LENGTH(TRIM(review_comment_message)) > 0
        THEN 1 ELSE 0
    END AS has_comment,

    review_creation_date::timestamp             AS created_at,
    review_answer_timestamp::timestamp          AS answered_at,

    -- Catégorisation de la note pour Power BI
    CASE
        WHEN review_score >= 4 THEN 'positive'
        WHEN review_score = 3  THEN 'neutral'
        ELSE                        'negative'
    END AS sentiment

FROM raw.raw_order_reviews
WHERE review_id IS NOT NULL
  AND order_id IS NOT NULL
  AND review_score BETWEEN 1 AND 5;
