# Report guide: how to read the Power BI report

## 1. Purpose and audience

The report answers one question for a Head of Complaints: **where do customers complain, how well are those complaints resolved, and how does that compare with the rest of the market?** The case-study company is Chime Financial Inc, but every page works for any of the 54 companies with at least 500 complaints.

- **Data:** CFPB consumer complaints, 1 Jan 2024 to 31 Dec 2025 (404,353 complaints), for three products: Credit Card; Checking or Savings Account; Money Transfer, Virtual Currency or Money Service.
- **Model:** one fact table (one row per complaint) and seven lookup tables, described in `03_model.md`. Measures are explained in `04_measures.md`.
- **Pages:** Overview, Root Causes, Focus vs Peers. Each page ends in a question the next page answers: *what is happening?* then *why?* then *how does it compare?*

## 2. Using the report

| Control | What it does |
|---|---|
| **Company** (pages 1–2) | Filters every visual on the page to one company. |
| **Focus company** (page 3) | Picks the company to compare against everyone else. It does not filter the peer side, which is why page 3 uses a separate slicer. |
| **Product** (pages 1–2) | Filters to one product, or all. |
| **Timeframe** (page 1) | Filters by year, quarter or month. |
| **Mode** (pages 2–3) | *Outlier-adjusted* (default) leaves out months flagged as unusual. *All months* keeps everything. |

**Why two modes.** Each product-month gets a flag when its complaint volume is far above normal (modified z-score above 3.5, per product). Three product-months are flagged: checking or savings accounts in January 2025, and money transfer in January and February 2025. The money transfer spikes were driven mainly by two companies, Block and Early Warning Services, and the checking spike by a few large banks (Navy Federal Credit Union and Capital One). If left in, those months would distort the peer benchmark. The flag is calculated per product across the whole market, so a spike at one company that does not move the product total, such as Chime in October 2025, is not removed.

**Why numbers differ between pages.** Page 1 shows all months (Chime relief 10.23%, 2,088 money transfer complaints), with the possibility to filter specific time periods within the 2 years. Page 3 is outlier-adjusted by default (10.12%, 1,989), with the possibility of switching *All months* which reproduces page 1 for Chime. Both pages are correct.

## 3. Page 1, Overview: what is happening?

!(../screenshots/Overview)

| Visual | What it shows | How to read it |
|---|---|---|
| **Complaints and outcomes by product** | Complaints, % responded on time, relief % and monetary relief % for each product. | Compare the measures between products. |
| **Monthly complaint volume** | Complaints per month with month-on-month change. | A big MoM swing is the cue to look for an event. The first month (January 2024) has no earlier month to be compared to so it is not included. |
| **Relief rate** | Relief % and monetary relief % by month. | Shows whether outcomes are improving or worsening over time. The two lines move together because monetary relief is a subset of relief. |
| **What customers complain about** | Issues by product with complaint count and share. | The share is within the product, so shares add to 100% inside each product. |

## 4. Page 2, Root Causes: why?

| Visual | What it shows | How to read it |
|---|---|---|
| **Issue Share %** | The top 10 issues' share of complaints in the selected product. | Choose one product to see which issue dominates it. With *All* products it mixes products, so prefer a single product. It counts all months and does not change with Mode. |
| **State map** | The relief gap vs peers (percentage points) for each state. | Darker means a larger gap. Only states where the company has at least 100 complaints are shown, so small states do not give noisy values. |
| **Relief rate by issue** | The company's relief % and the peer relief % for each top issue. | Look for issues where the blue bar is much shorter than the grey one. A missing blue bar means that the focus company has no relief cases for that issue. |

## 5. Page 3, Focus vs Peers: how does it compare?

| Visual | What it shows | How to read it |
|---|---|---|
| **Three cards** | Focus company relief %, peer relief % and the gap in percentage points. | A negative gap means the company resolves fewer complaints with relief than peers. |
| **Relief % by product** | Focus company (blue) vs peers (grey) for each product. | Shows whether the gap is spread across products or concentrated. |
| **Relief rate by company** | All 51 ranked companies, highest to lowest, with the focus company in blue. | Shows rank. A company can sit below the median without being the worst. |
| **Product table** | Complaints, relief %, peer relief % and the gap for each product. | The exact numbers behind the bars. |
| **Responded on time** | Share of the company's complaints answered within the CFPB deadline. | Chime's 100% shows that timeliness is not the issue, which is why relief is the focus. |

**Peers** are the other banks, fintechs and similar companies. Credit bureaus (Equifax, TransUnion, Experian) are tagged separately and not used as bank peers, and the focus company is excluded from its own benchmark.

## 6. Key definitions

| Term | Definition |
|---|---|
| Relief % | (Monetary relief + non-monetary relief) / complaints with an outcome. Complaints still in progress are excluded. |
| Monetary relief % | Monetary relief / complaints with an outcome. |
| Responded on time | Complaints marked "timely response" / all complaints. |
| Issue share | Complaints for an issue / complaints in the selected product. |
| Relief gap (pp) | Focus relief % minus peer relief %, in percentage points. |
| Unusual month | A product-month whose volume has a modified z-score above 3.5. |

Full formulas are in `04_measures.md`.

## 7. Data and limits

- Complaints are self-reported and are not a random sample of customers. 
- Volume depends on company size and events, not only service quality.
- There are no customer counts, so the report shows complaint counts and shares, not complaint rates.
- There is no response date, so response speed in days cannot be measured. Only the timely flag is used.
- A low relief rate can reflect the mix of complaints as well as how they are handled. The data cannot separate the two.
- US data only. Cleaning decisions are in `02_data_quality_log.md`.