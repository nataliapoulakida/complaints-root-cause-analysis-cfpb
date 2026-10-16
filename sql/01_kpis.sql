-- KPI and investigation queries for the CFPB complaints project.
-- Run with: python python\04_run_sql.py      (results are saved to sql/results/)
-- Table: complaints  (= data/clean/complaints_clean.csv, one row per complaint)
-- {{FOCUS}} is replaced by the case-study company (set in 04_run_sql.py).
--
-- KPI definitions (same as docs/01_brief.md):
--   timely %  = AVG(timely_flag) over all complaints
--   relief %  = AVG(relief_flag) over complaints with has_outcome = 1 (excludes "In progress")
--   peers     = company_type = 'Bank, fintech or other' AND company <> focus, compared within the same product

-- name: q01_monthly_volume
-- Story 1: monthly volume by product, with the unusual-month flag.
SELECT month_start, product, COUNT(*) AS complaints, MAX(unusual_month) AS unusual_month
FROM complaints
GROUP BY month_start, product
ORDER BY product, month_start;

-- name: q02_top_issues
-- Story 2: issues ranked within each product, with their share.
SELECT product, issue, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY product), 2) AS share_of_product_pct
FROM complaints
GROUP BY product, issue
ORDER BY product, complaints DESC;

-- name: q03_service_by_product
-- Story 3: service KPIs by product (all companies; credit bureaus included).
SELECT product, COUNT(*) AS complaints,
       ROUND(100.0 * AVG(timely_flag), 2) AS timely_pct,
       ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2) AS relief_pct,
       ROUND(100.0 * SUM(monetary_relief_flag) / SUM(has_outcome), 2) AS monetary_relief_pct
FROM complaints
GROUP BY product
ORDER BY product;

-- name: q04_company_vs_peers
-- Story 4: every ranked bank/fintech vs its product-matched peers (min 100 complaints per product).
WITH base AS (SELECT * FROM complaints WHERE company_type = 'Bank, fintech or other'),
prod AS (
  SELECT product, COUNT(*) AS n, SUM(timely_flag) AS timely, SUM(has_outcome) AS outc, SUM(relief_flag) AS relief
  FROM base GROUP BY product),
comp AS (
  SELECT company, product, COUNT(*) AS n, SUM(timely_flag) AS timely, SUM(has_outcome) AS outc, SUM(relief_flag) AS relief
  FROM base WHERE company_ranked = 1 GROUP BY company, product HAVING COUNT(*) >= 100)
SELECT c.company, c.product, c.n AS complaints,
       ROUND(100.0 * c.timely / c.n, 2) AS timely_pct,
       ROUND(100.0 * (p.timely - c.timely) / (p.n - c.n), 2) AS peer_timely_pct,
       ROUND(100.0 * c.relief / c.outc, 2) AS relief_pct,
       ROUND(100.0 * (p.relief - c.relief) / (p.outc - c.outc), 2) AS peer_relief_pct,
       ROUND(100.0 * c.relief / c.outc - 100.0 * (p.relief - c.relief) / (p.outc - c.outc), 2) AS relief_gap_pp
FROM comp c JOIN prod p USING (product)
ORDER BY c.product, c.n DESC;

-- name: q05_focus_gap_by_quarter
-- Investigation 1: is the focus company's relief gap stable over time? (by product and quarter)
WITH base AS (
  SELECT *, CAST(date_trunc('quarter', month_start) AS DATE) AS quarter
  FROM complaints WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1),
f AS (SELECT product, quarter, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company = '{{FOCUS}}' GROUP BY 1, 2),
p AS (SELECT product, quarter, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company <> '{{FOCUS}}' GROUP BY 1, 2)
SELECT f.product, f.quarter, f.n AS focus_complaints,
       ROUND(100.0 * f.relief / f.n, 2) AS focus_relief_pct,
       ROUND(100.0 * p.relief / p.n, 2) AS peer_relief_pct,
       ROUND(100.0 * f.relief / f.n - 100.0 * p.relief / p.n, 2) AS gap_pp
FROM f JOIN p USING (product, quarter)
ORDER BY f.product, f.quarter;

-- name: q06_focus_gap_by_issue
-- Investigation 2: same product AND same issue, focus company vs peers (min 50 focus complaints).
WITH base AS (SELECT * FROM complaints WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1),
f AS (SELECT product, issue, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company = '{{FOCUS}}' GROUP BY 1, 2),
p AS (SELECT product, issue, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company <> '{{FOCUS}}' GROUP BY 1, 2)
SELECT f.product, f.issue, f.n AS focus_complaints,
       ROUND(100.0 * f.relief / f.n, 2) AS focus_relief_pct,
       p.n AS peer_complaints,
       ROUND(100.0 * p.relief / p.n, 2) AS peer_relief_pct,
       ROUND(100.0 * f.relief / f.n - 100.0 * p.relief / p.n, 2) AS gap_pp
FROM f JOIN p USING (product, issue)
WHERE f.n >= 50
ORDER BY f.product, f.n DESC;

-- name: q07_focus_mix_adjusted
-- Investigation 2b: how much of the gap is just issue mix?
-- expected = what the focus company's relief rate would be if, for every (product, issue),
-- it closed with relief at the PEER rate. If expected is close to actual, the gap is mostly mix.
WITH base AS (SELECT * FROM complaints WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1),
f AS (SELECT product, issue, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company = '{{FOCUS}}' GROUP BY 1, 2),
p AS (SELECT product, issue, 1.0 * SUM(relief_flag) / COUNT(*) AS peer_rate FROM base WHERE company <> '{{FOCUS}}' GROUP BY 1, 2),
j AS (SELECT f.product, f.n, f.relief, p.peer_rate FROM f JOIN p USING (product, issue))
SELECT product, SUM(n) AS focus_complaints_compared,
       ROUND(100.0 * SUM(relief) / SUM(n), 2) AS actual_relief_pct,
       ROUND(100.0 * SUM(n * peer_rate) / SUM(n), 2) AS expected_at_peer_rates_pct,
       ROUND(100.0 * SUM(relief) / SUM(n) - 100.0 * SUM(n * peer_rate) / SUM(n), 2) AS gap_after_mix_pp
FROM j GROUP BY ROLLUP (product)
ORDER BY product NULLS LAST;

-- name: q08_focus_by_channel
-- Investigation 3a: how the complaint was submitted.
WITH base AS (SELECT * FROM complaints WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1),
f AS (SELECT submitted_via, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company = '{{FOCUS}}' GROUP BY 1),
p AS (SELECT submitted_via, COUNT(*) AS n, SUM(relief_flag) AS relief FROM base WHERE company <> '{{FOCUS}}' GROUP BY 1)
SELECT f.submitted_via, f.n AS focus_complaints,
       ROUND(100.0 * f.n / SUM(f.n) OVER (), 2) AS focus_share_pct,
       ROUND(100.0 * p.n / SUM(p.n) OVER (), 2) AS peer_share_pct,
       ROUND(100.0 * f.relief / f.n, 2) AS focus_relief_pct,
       ROUND(100.0 * p.relief / p.n, 2) AS peer_relief_pct
FROM f JOIN p USING (submitted_via)
ORDER BY f.n DESC;

-- name: q09_focus_by_response_type
-- Investigation 3b: how the company closes complaints (focus vs peers, within each product).
WITH base AS (SELECT * FROM complaints WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1),
f AS (SELECT product, company_response, COUNT(*) AS n FROM base WHERE company = '{{FOCUS}}' GROUP BY 1, 2),
p AS (SELECT product, company_response, COUNT(*) AS n FROM base WHERE company <> '{{FOCUS}}' GROUP BY 1, 2)
SELECT f.product, f.company_response, f.n AS focus_complaints,
       ROUND(100.0 * f.n / SUM(f.n) OVER (PARTITION BY f.product), 2) AS focus_share_pct,
       ROUND(100.0 * p.n / SUM(p.n) OVER (PARTITION BY f.product), 2) AS peer_share_pct
FROM f JOIN p USING (product, company_response)
ORDER BY f.product, f.n DESC;

-- name: q13_focus_vs_peers_outlier_adjusted
-- Investigation 4: sensitivity test. Same comparison as q04 but excluding the months flagged as unusual
-- (outlier-adjusted view). The unadjusted peer benchmark for money transfer is pulled down by one
-- very large company (Block) that closed almost every complaint "with explanation" in a flagged month.
WITH b AS (
  SELECT * FROM complaints
  WHERE company_type = 'Bank, fintech or other' AND has_outcome = 1)
SELECT product,
       SUM(CASE WHEN company = '{{FOCUS}}' THEN 1 ELSE 0 END) AS focus_complaints_all_months,
       ROUND(100.0 * SUM(CASE WHEN company = '{{FOCUS}}' THEN relief_flag END)
             / SUM(CASE WHEN company = '{{FOCUS}}' THEN 1 END), 2) AS focus_relief_all_months_pct,
       ROUND(100.0 * SUM(CASE WHEN company <> '{{FOCUS}}' THEN relief_flag END)
             / SUM(CASE WHEN company <> '{{FOCUS}}' THEN 1 END), 2) AS peer_relief_all_months_pct,
       ROUND(100.0 * SUM(CASE WHEN company = '{{FOCUS}}' AND unusual_month = 0 THEN relief_flag END)
             / SUM(CASE WHEN company = '{{FOCUS}}' AND unusual_month = 0 THEN 1 END), 2) AS focus_relief_adjusted_pct,
       ROUND(100.0 * SUM(CASE WHEN company <> '{{FOCUS}}' AND unusual_month = 0 THEN relief_flag END)
             / SUM(CASE WHEN company <> '{{FOCUS}}' AND unusual_month = 0 THEN 1 END), 2) AS peer_relief_adjusted_pct
FROM b GROUP BY product ORDER BY product;

-- name: q10_flagged_months_by_company
-- Story 5: who is behind the months flagged as unusual? (top 6 companies per flagged product-month)
WITH flagged AS (
  SELECT month_start, product, company, COUNT(*) AS complaints
  FROM complaints WHERE unusual_month = 1 GROUP BY 1, 2, 3),
ranked AS (
  SELECT *, SUM(complaints) OVER (PARTITION BY month_start, product) AS month_total,
         ROW_NUMBER() OVER (PARTITION BY month_start, product ORDER BY complaints DESC) AS rk
  FROM flagged)
SELECT month_start, product, rk AS rank, company, complaints,
       ROUND(100.0 * complaints / month_total, 1) AS share_of_month_pct, month_total
FROM ranked WHERE rk <= 6
ORDER BY product, month_start, rk;

-- name: q11_flagged_months_by_issue
-- Story 5: which issues are behind the flagged months? (top 5 issues per flagged product-month)
WITH flagged AS (
  SELECT month_start, product, issue, COUNT(*) AS complaints
  FROM complaints WHERE unusual_month = 1 GROUP BY 1, 2, 3),
ranked AS (
  SELECT *, SUM(complaints) OVER (PARTITION BY month_start, product) AS month_total,
         ROW_NUMBER() OVER (PARTITION BY month_start, product ORDER BY complaints DESC) AS rk
  FROM flagged)
SELECT month_start, product, rk AS rank, issue, complaints,
       ROUND(100.0 * complaints / month_total, 1) AS share_of_month_pct
FROM ranked WHERE rk <= 5
ORDER BY product, month_start, rk;

-- name: q12_reconciliation_totals
-- Story 6 / validation on Mon 19 Oct: totals to compare with Power BI.
SELECT 'all' AS cut, 'all' AS value, COUNT(*) AS complaints,
       ROUND(100.0 * AVG(timely_flag), 2) AS timely_pct,
       ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2) AS relief_pct
FROM complaints
UNION ALL
SELECT 'product', product, COUNT(*), ROUND(100.0 * AVG(timely_flag), 2), ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2)
FROM complaints GROUP BY product
UNION ALL
SELECT 'year', CAST(year(date_received) AS VARCHAR), COUNT(*), ROUND(100.0 * AVG(timely_flag), 2), ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2)
FROM complaints GROUP BY year(date_received)
UNION ALL
SELECT 'company_type', company_type, COUNT(*), ROUND(100.0 * AVG(timely_flag), 2), ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2)
FROM complaints GROUP BY company_type
UNION ALL
SELECT 'focus company', '{{FOCUS}}', COUNT(*), ROUND(100.0 * AVG(timely_flag), 2), ROUND(100.0 * SUM(relief_flag) / SUM(has_outcome), 2)
FROM complaints WHERE company = '{{FOCUS}}'
ORDER BY 1, 2;
