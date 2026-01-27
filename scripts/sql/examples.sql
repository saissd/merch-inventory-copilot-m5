-- Top items per store by revenue proxy (CTE + window function)
WITH daily AS (
  SELECT date, store_id, item_id, SUM(units) AS units, AVG(sell_price_filled) AS price
  FROM fact_sales
  GROUP BY 1,2,3
),
rev AS (
  SELECT store_id, item_id, SUM(units * price) AS revenue_proxy
  FROM daily
  GROUP BY 1,2
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY revenue_proxy DESC) AS rn
  FROM rev
)
SELECT * FROM ranked WHERE rn <= 20 ORDER BY store_id, rn;
