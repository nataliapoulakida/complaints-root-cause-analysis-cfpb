# Data dictionary

Source: CFPB Consumer Complaint Database (public), downloaded 14 Oct 2026. Six exports (three products, two years) were combined and cleaned by `python/01_combine_raw.py` and `python/03_clean.py` into `complaints_clean.csv` (404,353 rows, one per complaint). `python/05_build_model.py` then splits it into the star schema in `data/model/`. The `data/` folder is not in this repository, because it is large and public. Download the exports from the CFPB to rebuild it.

## Derived columns

These columns are not in the source data. They are created during cleaning and drive the report's measures.

| Column | Type | Definition |
|---|---|---|
| `timely_flag` | 0/1 | 1 when the CFPB field "Timely response?" is "Yes". |
| `has_outcome` | 0/1 | 1 when the company response is anything except "In progress". It is the denominator of relief rates. |
| `relief_flag` | 0/1 | 1 when the complaint was closed with monetary or non-monetary relief. |
| `monetary_relief_flag` | 0/1 | 1 when the complaint was closed with monetary relief. |
| `unusual_month` | 0/1 | 1 when the complaint's product-month has a modified z-score above 3.5 on monthly volume (unusually high volume only), calculated per product across all companies. |
| `company_type` | text | "Credit bureau" for Equifax, TransUnion and Experian, otherwise "Bank, fintech or other". Bureaus are kept out of the peer group. |
| `company_total_complaints` | integer | Number of complaints the company has in the whole dataset. |
| `company_ranked` | 0/1 | 1 when the company has at least 500 complaints. Only these companies appear in the company ranking. |
| `month_start` | date | First day of the month the complaint was received. |

## Fact table: `fact_complaints` (404,353 rows)

| Column | Description |
|---|---|
| `complaint_id` | CFPB complaint ID. Unique. |
| `date_key` | Date the complaint was received. Joins to `dim_date[date]`. |
| `product_key` | Joins to `dim_product`. |
| `issue_key` | Joins to `dim_issue`. |
| `company_key` | Joins to `dim_company`. |
| `state_key` | Joins to `dim_state`. |
| `channel_key` | Joins to `dim_channel`. |
| `response_key` | Joins to `dim_response`. |
| `tags` | "Servicemember", "Older American", both, or blank. Not used in the report. |
| `timely_flag`, `has_outcome`, `relief_flag`, `monetary_relief_flag`, `unusual_month` | See derived columns above. |

## Dimension tables

| Table | Rows | Columns | Notes |
|---|---|---|---|
| `dim_date` | 731 | `date`, `year`, `quarter`, `year_quarter`, `month_num`, `month_name`, `year_month`, `month_start` | One row per day, 1 Jan 2024 to 31 Dec 2025. |
| `dim_product` | 15 | `product_key`, `product`, `sub_product` | Three products: Credit card; Checking or savings account; Money transfer / virtual currency. |
| `dim_issue` | 99 | `issue_key`, `issue`, `sub_issue` | A missing sub-issue is shown as "Not specified". Money transfer has almost no sub-issues. |
| `dim_company` | 1,087 | `company_key`, `company`, `company_type`, `company_total_complaints`, `company_ranked` | Names that differed only in capitalisation or spacing were merged. Chime Financial Inc and Chime, Inc. are separate companies. |
| `dim_state` | 62 | `state_key`, `state` | Includes territories and military codes. A missing state is shown as "Unknown". |
| `dim_channel` | 4 | `channel_key`, `submitted_via` | Phone, Postal mail, Referral, Web. |
| `dim_response` | 5 | `response_key`, `company_response` | Closed with explanation; Closed with monetary relief; Closed with non-monetary relief; In progress; Untimely response. |

## Cleaning rules in one place

- Missing values stored as the text "None" were converted: sub-issue to "Not specified", and state, issue and sub-product to "Unknown". Tags and the company public response are left blank.
- Dates were converted to dates, and the time part dropped.
- `Days to send to company` is not used, because the data has no response date.
- Full list of decisions: `02_data_quality_log.md`.
