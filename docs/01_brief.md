# Project brief: where do customers complain, and what should we fix first?

**Author:** Natalia Poulakida | **Status:** Draft v1 | **Date:** 15 Oct 2026

## 1. Business context
A retail bank or fintech receives thousands of customer complaints, and regulators watch how fast and how fairly they are handled. Management needs to know which products and issues generate the most complaints, how the company's handling compares with peers, and where to act first.

*Case-study company: Chime Financial Inc. The dashboard itself is generic and works for any company in the data.*

## 2. Stakeholder and question
**Stakeholder:** Head of Complaints & Customer Operations.
**Core question:** Which products and issues drive complaints, where is our handling weaker than our peers and what should we fix first?

## 3. Data and scope
- CFPB Consumer Complaint Database (public), downloaded 14 Oct 2026.
- Data from 1 Jan 2024 to 31 Dec 2025
- Products: Credit Card; Checking or Savings Account; Money Transfer, Virtual Currency or Money Service 
- 404,353 complaints
- 1,088 company names
- All companies kept as the market benchmark. Credit bureaus are not used as bank peers and are tagged separately.
- **Out of scope:** narrative text, prediction, complaint rates per customer (no customer counts), other products, proving causes.

## 4. KPI definitions
| KPI | Definition |
|---|---|
| Complaint volume | Count of distinct Complaint IDs by Date received |
| Month-on-month change | (This month - Last month) / Last month |
| % timely response | Complaints with "Timely response?" = Yes / All complaints |
| % closed with relief | (Closed with monetary relief + Closed with non-monetary relief) / Complaints, excluding "In progress" |
| % monetary relief | Closed with monetary relief / Complaints, excluding "In progress" |
| Issue share | Complaints for an issue / Complaints in the selected product |
| Peer benchmark | The same KPI pooled across all other companies, excluding the focus company and the credit bureaus, calculated within the selected product(s) so that product mix does not distort the comparison. By default it excludes months flagged as unusual (outlier-adjusted view), so that one very large company in a flagged month cannot distort the benchmark |
| Unusual-month flag | A month is flagged for a product when its modified z-score exceeds 3.5. Modified z = 0.6745 x (monthly volume - median month) / median absolute deviation (MAD), computed per product over the 24 months |
| Outlier-adjusted view | Any KPI recalculated excluding flagged months |

A company appears in rankings only when it has at least 500 complaints in the chosen time window (smaller companies are grouped as "Other").

## 5. User stories and acceptance criteria
1. **As a Head of Complaints, I want a summary of volume and trend by product, so that I can see whether complaints are rising.** *Accepts when:* monthly volume by product is shown for Jan 2024 to Dec 2025, with a toggle that excludes flagged unusual months.
2. **As a Head of Complaints, I want to drill from product to issue to sub-issue, so that I can find the root causes.** *Accepts when:* the top issues per product are ranked with their share; money transfer stops at issue level because it has no sub-issues.
3. **As a Head of Complaints, I want % timely response and % closed with relief by product, so that I can judge service quality.** *Accepts when:* both KPIs match the definitions above and reconcile with the SQL queries.
4. **As a Head of Complaints, I want to compare my company with its peers on those KPIs, so that I know where we lag.** *Accepts when:* a company selector shows the company next to the peer benchmark, and only companies with 500+ complaints can be selected.
5. **As a Head of Complaints, I want to see what caused unusual spikes, so that I do not misread them as a service problem.** *Accepts when:* months flagged as unusual by the rule are visible on the trend and can be broken down by company and issue.
6. **As an analyst, I want every number to be traceable, so that stakeholders can trust it.** *Accepts when:* dashboard totals equal the SQL results, and data-quality decisions are documented.

## 6. Deliverables
- Cleaned dataset and Python/SQL scripts
- 3-page Power BI report; data dictionary
- Findings memo (1-2 pages) with top 3 findings and recommendations
- README and short screen recording.

## 7. Assumptions and limits
- Complaints are self-reported and not a random sample of customers.
- Volume depends on company size and on possible events, not only on service quality.
- The data has no response date, so response speed in days cannot be measured, therefore only the timely flag is used.
- Data is from the US.
