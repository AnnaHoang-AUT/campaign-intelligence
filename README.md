# Campaign Intelligence: From Audience to Attribution

**A SQL portfolio project built to demonstrate the difference between an analyst who reports campaign numbers and one who has actually run campaigns.**

10 years of managing campaigns means I don't just ask "what happened?" — I ask "was this audience even eligible to be targeted?", "would this revenue have happened anyway?", and "who should we target next?". This project is built around those questions, using a synthetic-but-realistic dataset (8,000 customers, 112 campaigns, ~450K rows across audience selection, sends, engagement and orders) modelled in SQLite.

## Why this project is different from a typical "SQL campaign analysis" portfolio piece

| Most portfolio projects | This project |
|---|---|
| Start from a clean "campaign results" table | Starts from a **candidate audience**, and models suppression, consent and control-group holdouts *before* a single send happens |
| Report revenue "attributed to" a campaign at face value | Tests whether that revenue was **incremental** using a genuine test-vs-control design |
| Pick one attribution model without saying so | Runs **three attribution models side by side** and shows how much they disagree |
| Stop at "here are the numbers" | Ends every tier with a **recommendation** — a next audience, a budget shift, a suppression rule |

## Schema

```
customers            -- who they are, consent flags, opt-out status
campaigns             -- channel, objective, cost, flight dates
audience_selection    -- EVERY candidate per campaign: sent / suppressed (+reason) / control_holdout
sends                  -- what was actually delivered
events                  -- opens, clicks
orders                   -- revenue, only campaign-tagged when the generator knows it was campaign-induced
```
Full DDL: [`schema.sql`](schema.sql). Data generator (documented, seeded, reproducible): [`generate_data.py`](generate_data.py). All analysis: [`queries.sql`](queries.sql).

The `audience_selection` table is the piece most portfolio projects skip. It's a direct translation of the campaign-ops work I did for years: verifying consent, applying frequency caps, excluding recent purchasers, and reconciling the final send count against the candidate pool — the work a client or compliance stakeholder actually asks about before a campaign goes out.

---

## Tier 1 — Baseline KPIs
*(what any SQL-literate analyst can produce)*

Open/click/conversion rates by campaign, revenue and cost by channel. Necessary, but this is where most SQL portfolio projects stop.

```
channel      campaigns  total_cost   campaign_tagged_revenue
Email             28    602,070          89,845
SMS               28    510,739          33,403
Paid Social       28  3,058,417          32,423
Display           28    915,858          12,915
```
Read at face value, Paid Social looks competitive with SMS. It isn't — see Tier 3.

## Tier 2 — Audience governance & segmentation
*(the work before the send — the part a marketing-operations background actually changes)*

**2.1 Audience reconciliation.** For every campaign, candidate pool → suppressed (by reason) → sent → control holdout. Example, Campaign #2: **2,800 candidates → only 272 sendable (9.7%)** once no-consent (517), frequency-cap (247) and opt-outs are removed. That's the number a stakeholder actually needs when a campaign under-delivers — not "the audience was small," but *why*.

**2.2 / 2.3 RFM segmentation**, built with `NTILE()` window functions rather than hardcoded thresholds, so it re-segments correctly as the customer base grows:

```
segment                             customers   revenue   % of revenue   % of customers
Core / steady                          1,725    140,973        31.5%          36.4%
Champions                                908    133,694        29.9%          19.2%
At-risk high-value (win back now)        569     81,218        18.2%          12.0%
Lapsed / low-value                       882     53,012        11.9%          18.6%
Recent, low-frequency (nurture)          651     38,334         8.6%          13.7%
```
The actionable read: **"At-risk high-value" is 12% of customers holding 18% of revenue** — a small, high-priority winback list, not a mass campaign.

## Tier 3 — Incrementality & attribution
*(the difference between "revenue happened near this campaign" and "this campaign caused revenue")*

**3.1 Test-vs-control incrementality.** Every campaign carries a ~10% holdout group logged in `audience_selection`. Comparing conversion rate of `sent` vs `control_holdout` within a 10-day window gives real causal lift, not a correlation:

```
campaign_id   treated_n   control_n   treated_conv%   control_conv%   incremental_lift(pts)
74               612         58           7.68            0.00            7.68
42               467         61           6.85            0.00            6.85
70              1036        100           6.18            1.00            5.18
```
This is the check that protects budget: a campaign can show "revenue" in Tier 1 and still have near-zero incremental lift once you compare against people who weren't sent anything.

**3.2 Attribution model comparison.** First-touch, last-touch and linear, computed side by side over a 25-day lookback:

```
channel        first_touch   last_touch   linear
Email             162,639      168,535    165,587
Paid Social        81,098       79,560     80,329
Display             59,641       49,216     54,429
SMS                 45,653       51,720     48,686
```
**Display swings by ~$10K (59.6K → 49.2K) depending on the model.** That's the conversation most dashboards never surface: which model you pick changes which channel looks like it's working, so a channel decision needs to say which model it's using — not just report "revenue."

**3.3 Blended CAC / ROAS.** Once cost is brought in, Paid Social's Tier-1 revenue lead disappears — Email returns **0.17 ROAS vs Paid Social's 0.03-range**, at a fraction of the spend.

## Tier 4 — Forward-looking recommendations
*(so what do we do next campaign)*

**4.1 Under-targeted lookalikes.** Customers who score like "Champions" on recency/frequency but have received ≤3 sends all-time — a ready-made audience for the next campaign, generated with a `LEFT JOIN` against send history rather than a manual list pull.

**4.2 Budget reallocation.** Every channel × objective combination's ROAS against the blended average, with an explicit `Increase budget` / `Reduce or re-test` flag — Email Retention and Cross-sell justify more spend; Display Acquisition (0.01 ROAS) doesn't.

---

## How to run it

```bash
python3 generate_data.py        # builds campaign_analytics.db (reproducible, seeded)
python3 run_queries.py          # runs every labelled query in queries.sql and prints results
```
No external services required — pure SQLite, pandas only used for pretty-printing results and generating the synthetic data.

## What I'd say about this in an interview

> "I built the audience-selection table first, before any results table, because that's the order the work actually happens in. The part I'm proudest of is the test-vs-control design — it's easy to show a campaign 'worked' by pointing at revenue near the send date; it's harder, and more useful to the business, to prove it wouldn't have happened anyway."
