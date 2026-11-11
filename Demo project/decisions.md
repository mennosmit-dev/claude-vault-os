---
type: decisions
project: "Demo project"
---

# Decisions Demo project

## Scope

- In: next-day rentals per station, 12 stations, weekdays and weekends.
- Out: pricing, new station locations, a dashboard (a CSV plus one page is enough for now).

## Working agreements

- Lena sends a fresh export every Monday.
- Every model is compared against the baseline on the same month before Ravi sees it.

## Decision log

| Date | Decision | Source |
| --- | --- | --- |
| 2026-11-04 | Forecast per day, not per hour, unless Ravi asks otherwise | [[2026-11-04 - Call - Ravi]] |
| 2026-11-06 | Metric: MAE per station-day; test month October 2026 | Baseline run |

## Related

- [[Workdoc - Demo project]]
