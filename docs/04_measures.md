# DAX measures

The Power BI model is a star schema: `fact_complaints` with `dim_date`, `dim_product`, `dim_issue`, `dim_company`, `dim_state`, `dim_channel` and `dim_response`. Two disconnected tables drive the controls: `ViewMode` (the Mode slicer) and `FocusSelector` (the company the report is "about", Chime by default).

This file covers the measures that carry the analysis. Formatting-only details are left out.

## Base measures

| Measure | What it answers |
|---|---|
| `Complaints` | Number of complaints in the current filter context. |
| `Relief %` | Share of complaints with an outcome that ended in any relief (monetary or non-monetary). |
| `Monetary Relief %` | Same, but monetary relief only. |
| `Responded on time` | Share of complaints the company answered within the CFPB deadline. |
| `Complaints Prev Month`, `MoM %` | Month-over-month change in volume. |

```dax
Relief % = DIVIDE ( SUM ( fact_complaints[relief_flag] ), SUM ( fact_complaints[has_outcome] ) )
```

The denominator is complaints **with an outcome**, not all complaints, so complaints still in progress do not count as "no relief".

```dax
Issue Share % =
DIVIDE ( [Complaints], CALCULATE ( [Complaints], REMOVEFILTERS ( dim_issue ) ) )
```

Only the issue filter is removed from the denominator. When a product is selected, the share is therefore **within that product**, not of all complaints.

## Outlier-adjusted view

Each product-month gets an `unusual_month` flag (modified z-score above 3.5 on monthly volume, per product). The Mode slicer decides whether flagged months are included:

```dax
Exclude Flagged Months =
SELECTEDVALUE ( ViewMode[Mode], "Outlier-adjusted" ) = "Outlier-adjusted"

Relief % (view) =
VAR maxFlag = IF ( [Exclude Flagged Months], 0, 1 )
RETURN CALCULATE ( [Relief %], fact_complaints[unusual_month] <= maxFlag )
```

`Complaints (view)` follows the same pattern. The default is *Outlier-adjusted*, so a single one-off spike (for example Chime in Oct 2025) does not dominate the comparison. *All months* shows the unfiltered picture.

## Focus company vs peers

```dax
Selected Focus =
SELECTEDVALUE ( FocusSelector[Focus company], "Chime Financial Inc" )

Peer Relief % =
VAR focus = [Selected Focus]
VAR maxFlag = IF ( [Exclude Flagged Months], 0, 1 )
RETURN
    CALCULATE (
        [Relief %],
        dim_company[company_type] = "Bank, fintech or other",
        dim_company[company] <> focus,
        fact_complaints[unusual_month] <= maxFlag
    )

Relief Gap (pp) = ( [Chime Financial Inc Relief %] - [Peer Relief %] ) * 100
```

- The focus company comes from a disconnected slicer table, so choosing a company changes these measures without filtering the rest of the report.
- The peer pool is all other banks, fintechs and similar companies. It excludes the focus company, so it is not diluted by it.
- `Chime Financial Inc Relief %`, `Chime Financial Inc Complaints (view)` and `Focus Timely %` are the focus-company equivalents of the base measures (same logic, filtered to `[Selected Focus]`). Despite the name they follow the selector.
- `Map Gap (pp)` returns the gap only where the focus company has at least 100 complaints, so thin states do not show noisy gaps.

## Why two filters rather than one slicer

`dim_company[company]` would filter every visual, including the peer side of the comparison. Putting the focus company in its own disconnected table lets each measure compare the focus company with everyone else.
