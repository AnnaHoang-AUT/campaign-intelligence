# Campaign Intelligence: From Audience to Decisions

**An end-to-end marketing analytics and decision-support web application built with SQL, Python, pandas, Streamlit and Plotly.**

[**Explore the interactive web app ↗**](https://campaign-intelligence-annahoang.streamlit.app/), [**Connect on LinkedIn ↗**](https://www.linkedin.com/in/anna-hoang-aut/)

> **Portfolio note:** This project uses synthetic data to demonstrate an end-to-end analytical workflow, from audience eligibility and campaign performance to measurement, data validation and business decisions. It does not represent results from a live client campaign.

## Why I built it

My 12 years in marketing, including over 6 years in campaign delivery, have shaped how I approach data analysis.

When clients want to understand how effective their campaigns were, I look beyond headline metrics such as reach, opens and revenue recorded after launch. I want to understand the full campaign journey: 
  * What happened before the campaign went live? 
  * Was the intended audience eligible and correctly selected? 
  * If results fell short, where might the problem have occurred? 
  * Did the campaign generate additional purchases, or might some customers have purchased anyway? 
  * What can we learn from promising campaigns, and where should the next marketing dollars go?

These questions inspired me to build Campaign Intelligence. I wanted to connect my practical understanding of campaign operations with the analytical and technical skills I developed through my Master of Analytics.

The project reflects an approach I value: starting with the business problem, examining the underlying data carefully, investigating possible root causes, validating findings and translating them into practical, evidence-informed recommendations.

## At a glance

| Project scope | Details |
|---|---|
| Data | Synthetic portfolio of **8,000 customers and 112 campaigns**, across Email, SMS, Paid Social and Display |
| Database | **SQLite** with customer, campaign, audience-selection, send, event and order records |
| Analysis | **SQL** for joins, aggregation, audience reconciliation, segmentation and campaign-level comparisons |
| Application | **Python, pandas, Streamlit and Plotly** for data preparation and an interactive decision dashboard |
| Delivery | Published CSV exports, **GitHub** version control and **Streamlit Community Cloud** deployment |

## The questions the dashboard answers

1. **Overview:** What do campaign cost, campaign-tagged revenue and channel performance tell us about the historical portfolio?
2. **Trend:** How do recorded campaign costs and tagged ROAS vary by campaign launch month?
3. **Channel economics:** How do channels compare on recorded cost, tagged orders and tagged ROAS?
4. **Audience & eligibility:** How does the candidate audience reconcile to recorded sends, holdouts and suppressions? Which recorded exclusion reasons explain the gap?
5. **Customer priorities:** Which historical purchasing segments may warrant closer attention, subject to fresh eligibility and consent checks?
6. **Observed lift:** How do recorded-send and holdout conversion rates compare, and how uncertain are the campaign-level estimates?
7. **Decisions:** Which campaigns warrant review, improved measurement or a controlled re-test? Which customer opportunities require an eligibility review?
8. **Data quality:** Do the reported aggregate counts and costs reconcile across the published exports?

The dashboard is designed as a **decision workspace**, not just a collection of charts. Each view connects the metric to its definition, an important limitation and a business question worth investigating.

## Data model and workflow

```text
customers           Customer details, signup dates, consent and opt-out indicators
campaigns           Channel, objective, dates and recorded cost
audience_selection  Candidate customer–campaign records: sent, holdout or suppressed
sends               Recorded campaign sends (not proof of delivery)
events              Recorded engagement events, such as opens and clicks
orders              Purchase records, revenue and any campaign ID tag
```

The audience-selection table matters to the way I approach the problem. It lets me investigate the journey **before** a send: candidate audience → eligibility and suppression decisions → recorded sends or holdouts. Counts across campaigns are *customer–campaign records*, not necessarily distinct customers. Historical contactability indicators do not replace a current permission or eligibility check.

The analysis is generated from the SQLite project and published as CSV exports for the Streamlit app. The repository also includes the schema, synthetic-data generator and SQL analysis files: [`schema.sql`](schema.sql), [`generate_data.py`](generate_data.py) and [`queries.sql`](queries.sql).

## Selected findings and how I interpret them

The current dashboard reports **$347,064 in recorded campaign cost** and approximately **$168,587 in campaign-tagged revenue** across 112 campaigns, equivalent to **0.49× portfolio tagged ROAS**. These are historical synthetic figures, not a profitability or causal-impact estimate.

| Channel | Campaigns | Recorded cost | Campaign-tagged revenue | Tagged ROAS |
|---|---:|---:|---:|---:|
| Email | 28 | $12,116 | $89,845 | 7.42× |
| SMS | 28 | $26,456 | $33,403 | 1.26× |
| Paid Social | 28 | $178,243 | $32,423 | 0.18× |
| Display | 28 | $130,249 | $12,915 | 0.10× |

These differences are a starting point for investigation, **not an automatic instruction to shift budget**. I would first check campaign objectives, audience composition, eligibility, cost allocation and measurement consistency, then use an appropriately designed test to evaluate potential incremental impact. The dashboard's **1.00× ROAS line is illustrative**: revenue equal to recorded campaign cost, before product costs or margin.

The observed-lift view compares conversion in the recorded-send and holdout groups over the original project's **11-calendar-date observation window** (campaign start through start + 10 days, inclusive). Campaign-level uncertainty is shown using **95% Newcombe intervals based on Wilson bounds**. An exploratory positive signal requires a lower interval bound above zero and at least 30 holdouts. Customers can occur in multiple campaigns and holdouts may have other campaign exposure, so these comparisons **do not prove isolated causal lift or incremental revenue**.

The separate companion analysis explores **first-touch, last-touch and linear send-based attribution** over a 25-day lookback. Those *attributed* revenue figures are distinct from the Streamlit dashboard's *campaign-tagged* revenue figures; they should not be mixed or described as proof of causation.

## Data quality and limitations

The Data Quality page runs **six aggregate reconciliation checks** across campaign counts, portfolio cost, channel and monthly totals, and cost-per-tagged-order rounding. These are useful checks of reporting consistency, **not a complete audit** of send-level matching, consent compliance, experiment validity or data generation.

All data is synthetic; some generator assumptions can affect eligibility and channel comparisons. A send record does not guarantee delivery or viewing. Historical revenue is not customer lifetime value, and segment labels describe past behaviour rather than predicting future behaviour. Monthly spend groups each campaign's recorded cost by **launch month**, not the timing of actual cash expenditure.

## Tools and skills demonstrated

**SQL / SQLite:** relational schema, joins, CTEs and window functions (including `NTILE()`), segmentation, aggregation and reconciliation.  
**Python / pandas:** data preparation, export handling and validation logic.  
**Streamlit / Plotly:** interactive filtering, visualisation, metrics and decision-focused presentation.  
**GitHub / Streamlit Community Cloud:** project documentation, version control and deployment.  
**Analytical practice:** clear metric definitions, controlled-comparison interpretation, investigation of data gaps and communication of practical recommendations.

## Run locally

With Python installed, clone the repository and install the dashboard dependencies:

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard reads the published files in `powerbi_exports/`. To rebuild the synthetic database and run the original SQL workflow, use the generator and query runner supplied in the repository:

```bash
python generate_data.py
python run_queries.py
```

## About me: [**Connect on LinkedIn ↗**](https://www.linkedin.com/in/anna-hoang-aut/)

I'm **Anna (Huong) Hoang**, a 12-year experience marketing professional with a Master of Analytics (First Class Honours), developing my career in Business Intelligence and data science. I enjoy work that connects careful technical analysis with an understanding of the real process behind the data—and makes the resulting evidence useful to the people making decisions.

**Explore:** [Live dashboard](https://campaign-intelligence-annahoang.streamlit.app/), 
