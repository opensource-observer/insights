-- optimism.prices.token_to_usd_monthly
-- Sample response:
-- {
--   "date": "2026-01-01",
--   "token": "ETH",
--   "price": 1000
-- },
-- {
--   "date": "2026-01-01",
--   "token": "OP",
--   "price": 1.5
-- },


SELECT
  DATE_TRUNC('MONTH', date) AS date,
  token,
  AVG(price) AS price
FROM optimism.prices.token_to_usd_daily
GROUP BY 1,2
ORDER BY 1,2