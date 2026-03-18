CREATE TEMP TABLE tmp_json (content text);
\copy tmp_json FROM 'G:/Заказчики.json' CSV QUOTE E'\b' ESCAPE E'\b' DELIMITER '|' ENCODING 'UTF8'

INSERT INTO customers (name, inn, address, phone, issalesman, isbuyer)
SELECT 
    obj->>'name' AS name, 
    obj->>'inn' AS inn, 
    obj->>'addres' AS address,
    obj->>'phone' AS phone, 
    (obj->>'salesman')::boolean AS issalesman, 
    (obj->>'buyer')::boolean AS isbuyer
FROM (
    SELECT jsonb_array_elements(string_agg(content, '')::jsonb) AS obj 
    FROM tmp_json
) AS subquery;

DROP TABLE tmp_json;