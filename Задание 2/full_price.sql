WITH actual_prices AS (
    SELECT DISTINCT ON (nomenc_id) nomenc_id, price
    FROM prices ORDER BY nomenc_id, price_date DESC
),
product_costs AS (
    SELECT s.nomenc_id AS prod_id,
           SUM(sm.amount * ap.price) / s.amount AS unit_cost
    FROM specifications s
    JOIN spec_materials sm ON s.id = sm.spec_id
    JOIN actual_prices ap ON sm.nomenc_id = ap.nomenc_id
    GROUP BY s.id, s.nomenc_id, s.amount
)
SELECT o.order_number, c.name,
       SUM(ol.amount * pc.unit_cost) AS total_material_value
FROM orders o
JOIN customers c ON o.customer = c.id
JOIN order_list ol ON o.id = ol.order_id
JOIN product_costs pc ON ol.nomenc_id = pc.prod_id
GROUP BY o.order_number, c.name;