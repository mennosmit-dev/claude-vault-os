---
type: workdoc
status: active
summary: "Daily rental demand forecast per station for a fictional bike rental shop, to plan bike moves overnight."
---

# Demo project

*Fictional example. Names, data and numbers are made up.*

## What it is

A bike rental shop with 12 stations runs out of bikes at busy stations by 10:00 on weekdays. Goal: a next-day forecast of rentals per station, good enough to plan overnight moves with one van.

## Status

Baseline done (same weekday last week). First gradient boosting model is next, once the weather join works.

## People

- Ravi: owner, decides on the van schedule.
- Lena: operations, exports rental data from the booking system.

## Links

- Data: `_code/data/rentals_2025-2026.csv` (export by Lena, 2026-11-03; not included in this demo)
- Code: `_code/` (not included in this demo)
- Kickoff: [[2026-11-04 - Call - Ravi]]

## Open questions

- Does the van route need the forecast by 21:00, or is 22:00 fine? (asked 2026-11-04, waiting)
- Are rentals during the October maintenance week usable?

#### Log

- [2026-11-04] Kickoff with Ravi: scope is next-day forecast per station, one van. [[2026-11-04 - Call - Ravi]]
- [2026-11-06] Baseline "same weekday last week": MAE 6.8 rentals per station-day on Oct 2026 (measured).
- [2026-11-10] Weather join fails for 2 stations without coordinates; asked Lena.

## Related

- [[tasks]] · [[decisions]] · [[session]] · [[Home]]
