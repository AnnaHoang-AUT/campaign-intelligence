"""
Generates a realistic synthetic marketing-campaign dataset and loads it into
campaign_analytics.db (SQLite). The data is built so that the SQL in
queries.sql has real, non-trivial patterns to uncover:

  - a genuine holdout/control group on most campaigns (so incrementality
    analysis is meaningful, not just a formula)
  - suppression logic applied BEFORE send (consent, opt-out, frequency cap,
    recent-purchase exclusion) with reasons logged
  - customer-level propensity to engage/convert that varies by acquisition
    channel and lifecycle, so segmentation queries find real signal
  - multiple touches before some conversions, so attribution models
    (first-touch vs last-touch vs linear) genuinely disagree

Deterministic (seeded) so results are reproducible.
"""

import sqlite3
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)
DB_PATH = "campaign_analytics.db"

# ---------------------------------------------------------------------------
# 1. CUSTOMERS
# ---------------------------------------------------------------------------
N_CUST = 8000
START = date(2023, 1, 1)
END = date(2025, 8, 31)
span_days = (END - START).days

channels_acq = ["Paid Social", "Organic Search", "Referral", "Events", "Paid Search"]
acq_weights = [0.32, 0.28, 0.14, 0.08, 0.18]
regions = ["Auckland", "Wellington", "Christchurch", "Hamilton", "Other NZ"]
region_weights = [0.38, 0.16, 0.14, 0.08, 0.24]

signup_offset = rng.integers(0, span_days - 30, N_CUST)
signup_date = [START + timedelta(days=int(d)) for d in signup_offset]

# latent propensities (not exposed in the schema - they just drive behaviour)
engagement_propensity = np.clip(rng.beta(2, 4, N_CUST), 0.02, 0.95)
value_propensity = np.clip(rng.gamma(2.0, 1.0, N_CUST), 0.2, 8)

acquisition_channel = rng.choice(channels_acq, N_CUST, p=acq_weights)
region = rng.choice(regions, N_CUST, p=region_weights)
birth_year = rng.integers(1955, 2006, N_CUST)

consent_email = rng.random(N_CUST) < 0.90
consent_sms = rng.random(N_CUST) < 0.55

opted_out = rng.random(N_CUST) < 0.06
opt_out_offset = rng.integers(30, span_days, N_CUST)
opted_out_date_obj = [
    (signup_date[i] + timedelta(days=int(opt_out_offset[i])))
    if opted_out[i] and (signup_date[i] + timedelta(days=int(opt_out_offset[i]))) <= END
    else None
    for i in range(N_CUST)
]
opted_out_date = [d.isoformat() if d is not None else None for d in opted_out_date_obj]

customers = pd.DataFrame({
    "customer_id": np.arange(1, N_CUST + 1),
    "signup_date": [d.isoformat() for d in signup_date],
    "acquisition_channel": acquisition_channel,
    "region": region,
    "birth_year": birth_year,
    "consent_email": consent_email.astype(int),
    "consent_sms": consent_sms.astype(int),
    "opted_out_date": opted_out_date,
})

# ---------------------------------------------------------------------------
# 2. CAMPAIGNS
# ---------------------------------------------------------------------------
CH = ["Email", "SMS", "Paid Social", "Display"]
OBJ = ["Acquisition", "Retention", "Winback", "Cross-sell"]

campaign_rows = []
cid = 1
cur = date(2024, 1, 1)
while cur <= date(2025, 8, 1):
    for ch in CH:
        obj = rng.choice(OBJ, p=[0.25, 0.35, 0.2, 0.2])
        dur = int(rng.integers(5, 15))
        cost_base = {"Email": 400, "SMS": 900, "Paid Social": 6000, "Display": 4500}[ch]
        cost = float(cost_base * rng.uniform(0.7, 1.4))
        campaign_rows.append({
            "campaign_id": cid,
            "campaign_name": f"{obj} - {ch} - {cur.strftime('%b %Y')}",
            "channel": ch,
            "objective": obj,
            "start_date": cur.isoformat(),
            "end_date": (cur + timedelta(days=dur)).isoformat(),
            "cost": round(cost, 2),
        })
        cid += 1
    cur = cur + timedelta(days=21)  # roughly monthly waves, staggered

campaigns = pd.DataFrame(campaign_rows)

# ---------------------------------------------------------------------------
# 3. BASELINE (ORGANIC) ORDERS  -- exist independent of any campaign
# ---------------------------------------------------------------------------
baseline_orders = []
oid = 1
cust_lookup = customers.set_index("customer_id")
for cust_id in customers["customer_id"]:
    prop = value_propensity[cust_id - 1]
    n_baseline = rng.poisson(0.4 + 0.6 * engagement_propensity[cust_id - 1])
    su = date.fromisoformat(cust_lookup.loc[cust_id, "signup_date"])
    for _ in range(n_baseline):
        offset = int(rng.integers(0, max((END - su).days, 1)))
        odate = su + timedelta(days=offset)
        if odate > END:
            continue
        revenue = round(float(rng.lognormal(mean=3.6, sigma=0.5) * (0.6 + 0.4 * prop)), 2)
        baseline_orders.append((oid, cust_id, odate.isoformat(), revenue))
        oid += 1

# ---------------------------------------------------------------------------
# 4. AUDIENCE SELECTION, SUPPRESSION, SENDS, EVENTS, CAMPAIGN-LIFT ORDERS
# ---------------------------------------------------------------------------
base_orders_df = pd.DataFrame(baseline_orders, columns=["order_id", "customer_id", "order_date", "revenue"])
base_orders_df["order_date"] = pd.to_datetime(base_orders_df["order_date"])
purchases_by_cust = base_orders_df.groupby("customer_id")["order_date"].apply(list).to_dict()

last_send_date = {}   # customer_id -> most recent send date (any campaign) for frequency cap
audience_rows = []
send_rows = []
event_rows = []
lift_order_rows = []
sel_id = 1
send_id = 1
event_id = 1
oid = base_orders_df["order_id"].max() + 1 if len(base_orders_df) else 1

CTRL_RATE = 0.10
FREQ_CAP_DAYS = 9

channel_open_rate = {"Email": 0.34, "SMS": 0.55, "Paid Social": 0.18, "Display": 0.09}
channel_ctr_given_open = {"Email": 0.22, "SMS": 0.30, "Paid Social": 0.12, "Display": 0.07}
channel_lift = {"Email": 0.045, "SMS": 0.06, "Paid Social": 0.03, "Display": 0.018}
obj_lift_mult = {"Acquisition": 0.7, "Retention": 1.15, "Winback": 1.3, "Cross-sell": 1.0}
obj_aov_mult = {"Acquisition": 0.8, "Retention": 1.1, "Winback": 0.95, "Cross-sell": 1.25}

campaigns_sorted = campaigns.sort_values("start_date").to_dict("records")

for camp in campaigns_sorted:
    c_start = date.fromisoformat(camp["start_date"])
    consent_col = "consent_sms" if camp["channel"] == "SMS" else "consent_email"

    # candidate pool size depends on channel reach
    pool_frac = {"Email": 0.55, "SMS": 0.35, "Paid Social": 0.45, "Display": 0.4}[camp["channel"]]
    candidates = customers.sample(frac=pool_frac, random_state=int(camp["campaign_id"]))

    for _, row in candidates.iterrows():
        cust_id = int(row["customer_id"])
        su = date.fromisoformat(row["signup_date"])
        reason = None
        if su > c_start:
            reason = "not_yet_signed_up"
        elif pd.notna(row["opted_out_date"]) and date.fromisoformat(row["opted_out_date"]) <= c_start:
            reason = "opted_out"
        elif row[consent_col] == 0:
            reason = "no_consent"
        elif cust_id in last_send_date and (c_start - last_send_date[cust_id]).days < FREQ_CAP_DAYS:
            reason = "frequency_cap"
        elif camp["objective"] == "Acquisition":
            recent_purchases = [d for d in purchases_by_cust.get(cust_id, [])
                                 if 0 <= (pd.Timestamp(c_start) - d).days <= 30]
            if recent_purchases:
                reason = "recent_purchase_exclusion"

        if reason is not None:
            audience_rows.append((sel_id, camp["campaign_id"], cust_id, "suppressed", reason))
            sel_id += 1
            continue

        is_control = rng.random() < CTRL_RATE
        if is_control:
            audience_rows.append((sel_id, camp["campaign_id"], cust_id, "control_holdout", None))
            sel_id += 1
            continue

        # ---- SENT ----
        audience_rows.append((sel_id, camp["campaign_id"], cust_id, "sent", None))
        sel_id += 1
        send_offset = int(rng.integers(0, 4))
        s_date = c_start + timedelta(days=send_offset)
        send_rows.append((send_id, camp["campaign_id"], cust_id, s_date.isoformat(), camp["channel"]))
        last_send_date[cust_id] = s_date

        prop = engagement_propensity[cust_id - 1]
        opened = rng.random() < channel_open_rate[camp["channel"]] * (0.5 + 1.2 * prop)
        clicked = False
        if opened:
            event_rows.append((event_id, send_id, "open", s_date.isoformat())); event_id += 1
            clicked = rng.random() < channel_ctr_given_open[camp["channel"]] * (0.5 + 1.2 * prop)
            if clicked:
                event_rows.append((event_id, send_id, "click", s_date.isoformat())); event_id += 1

        # campaign-induced incremental order within a 10-day attribution window
        lift_p = channel_lift[camp["channel"]] * obj_lift_mult[camp["objective"]] * (0.4 + 1.3 * prop)
        lift_p *= 1.6 if clicked else (1.0 if opened else 0.5)
        if rng.random() < lift_p:
            conv_offset = int(rng.integers(0, 10))
            c_date = s_date + timedelta(days=conv_offset)
            if c_date <= END:
                revenue = round(float(rng.lognormal(mean=3.7, sigma=0.45)
                                       * (0.6 + 0.4 * value_propensity[cust_id - 1])
                                       * obj_aov_mult[camp["objective"]]), 2)
                lift_order_rows.append((oid, cust_id, c_date.isoformat(), revenue, camp["campaign_id"]))
                oid += 1
        send_id += 1

# ---------------------------------------------------------------------------
# 5. ASSEMBLE FINAL TABLES
# ---------------------------------------------------------------------------
audience_selection = pd.DataFrame(
    audience_rows, columns=["selection_id", "campaign_id", "customer_id", "status", "suppression_reason"]
)
sends = pd.DataFrame(send_rows, columns=["send_id", "campaign_id", "customer_id", "send_date", "channel"])
events = pd.DataFrame(event_rows, columns=["event_id", "send_id", "event_type", "event_date"])

lift_orders = pd.DataFrame(lift_order_rows, columns=["order_id", "customer_id", "order_date", "revenue", "campaign_id"])
base_orders_df["campaign_id"] = None
base_orders_df["order_date"] = base_orders_df["order_date"].dt.strftime("%Y-%m-%d")
orders = pd.concat([base_orders_df, lift_orders], ignore_index=True).sort_values("order_id")

customers = customers.drop(columns=[])  # keep as is

# ---------------------------------------------------------------------------
# 6. WRITE TO SQLITE
# ---------------------------------------------------------------------------
conn = sqlite3.connect(DB_PATH)
customers.to_sql("customers", conn, if_exists="replace", index=False)
campaigns.to_sql("campaigns", conn, if_exists="replace", index=False)
audience_selection.to_sql("audience_selection", conn, if_exists="replace", index=False)
sends.to_sql("sends", conn, if_exists="replace", index=False)
events.to_sql("events", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
conn.commit()

for t in ["customers", "campaigns", "audience_selection", "sends", "events", "orders"]:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {n:,} rows")

conn.close()
print("\nDatabase written to", DB_PATH)
