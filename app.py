"""Campaign Intelligence — refined Streamlit portfolio dashboard.

The public dashboard uses published synthetic CSV exports. Run locally with:
    python -m streamlit run app.py --server.port 8503

For Streamlit Community Cloud, save this file as app.py at the repository root.
"""
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Campaign Intelligence | Anna Hoang",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#142B3B"
TEAL = "#087F79"
BLUE = "#2879C5"
PURPLE = "#7C62B3"
ORANGE = "#E58A39"
CHANNEL_COLORS = {
    "Email": TEAL,
    "SMS": PURPLE,
    "Paid Social": BLUE,
    "Display": ORANGE,
}
CHANNEL_ORDER = ["Email", "SMS", "Paid Social", "Display"]
REPORT_DATE = "23 September 2026"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "powerbi_exports"

st.markdown(
    """
    <style>
      /* Original Campaign Intelligence palette and compact information hierarchy. */
      :root { --ci-navy: #112938; --ci-sidebar: #172F3F; --ci-teal: #087F79; --ci-border: #D8E5ED; }
      .stApp { background-color: #F6F9FC; color: var(--ci-navy); }
      /* Keep Streamlit's own toolbar on its own light row. The branded bar
         below is part of the page, not underneath Streamlit's fixed header. */
      [data-testid="stHeader"] { background: #F6F9FC; }
      section[data-testid="stSidebar"] { background: #172F3F; border-right: 1px solid #254556; }
      section[data-testid="stSidebar"] * { color: #EDF7FA; }
      section[data-testid="stSidebar"] [data-testid="stRadio"] label { color: #EDF7FA; }
      section[data-testid="stSidebar"] div[role="radiogroup"] label {
          border-left: 3px solid transparent; border-radius: 6px; padding: 7px 9px;
      }
      section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
          background-color: #264C5B; border-left-color: #55CFB3;
      }
      .block-container {
          padding-top: 4.4rem !important;
          padding-bottom: 2rem;
          max-width: 1480px;
      }
      h1 { font-size: 2.1rem !important; font-weight: 760 !important; letter-spacing: -.025em; }
      h2, h3 { color: #142B3B !important; letter-spacing: -.015em; }
      h3 { font-size: 1.32rem !important; }
      div[data-testid="stMetric"] {
          border: 1px solid var(--ci-border); border-top: 2px solid #CEE0E6;
          border-radius: 8px; background: #FFF; padding: 17px 16px; min-height: 106px;
      }
      div[data-testid="stMetricLabel"] { font-size: .89rem; }
      div[data-testid="stMetricValue"] { color: #152D3D; }
      div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div .ci-panel-mark) {
          background: #FFF;
      }
      .ci-topbar {
          background: #112938; padding: 15px 18px; border-radius: 6px; margin-bottom: 22px;
          min-height: 56px; box-sizing: border-box;
          color: #E9F5F7; display: flex; align-items:center; justify-content: space-between; gap: 12px;
          font-family: 'Segoe UI', Arial, sans-serif;
      }
      .ci-topbar-left { display: flex; gap: 10px; align-items: center; font-size: .91rem; letter-spacing: .085em; }
      .ci-topbar-icon { color: #5DCEB8; font-size: 1.55rem; line-height: 1; }
      .ci-topbar-right { display: flex; align-items: center; gap: 18px; font-size: .78rem; white-space: nowrap; }
      .ci-synth { border: 1px solid #45766F; color: #A5F1E1; padding: 5px 8px; border-radius: 4px; letter-spacing: .07em; }
      /* Only the five Overview KPIs are dark; other pages retain light metrics. */
      .ci-kpi-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 16px;
          margin: 16px 0 24px;
      }
      .ci-kpi-card {
          background: #142B3B;
          color: #FFFFFF;
          border: 1px solid #274859;
          border-top: 3px solid #5CD4B8;
          border-radius: 8px;
          padding: 17px 16px 18px;
          min-height: 132px;
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          gap: 14px;
      }
      .ci-kpi-label {
          color: #70E3C7;
          font-family: 'Segoe UI', Arial, sans-serif;
          font-size: 1.025rem;
          font-weight: 750;
          line-height: 1.3;
      }
      .ci-kpi-number {
          color: #FFFFFF;
          font-family: 'Segoe UI', Arial, sans-serif;
          font-size: clamp(1.65rem, 2.15vw, 2.15rem);
          font-weight: 770;
          letter-spacing: -.035em;
          line-height: 1.14;
          font-variant-numeric: tabular-nums;
          white-space: nowrap;
      }
      .ci-side-brand { font-size: .95rem; letter-spacing: .07em; font-weight: 770; line-height: 1.4; margin-bottom: 9px; }
      .ci-side-brand span { color:#64D3BC; font-size: 1.3rem; margin-right: 6px; }
      .ci-sidebar-rule { border-top:1px solid #385565; margin:23px 0 16px; }
      .ci-side-bars { display:flex; align-items:flex-end; gap:4px; height:32px; margin-bottom:13px; }
      .ci-side-bars i { width:7px; background:#61D2BC; display:block; }
      .ci-side-bars i:nth-child(1){height:12px} .ci-side-bars i:nth-child(2){height:22px}
      .ci-side-bars i:nth-child(3){height:17px} .ci-side-bars i:nth-child(4){height:29px}
      .ci-eyebrow { color: var(--ci-teal); text-transform: uppercase; font-weight: 760; letter-spacing: .15em; font-size: .75rem; margin-bottom: 2px; }
      .ci-banner { background: #E9F8F5; border: 1px solid #BDE4DB; border-radius: 7px; padding: 14px 16px; margin: 14px 0 20px; color: #17394A; }
      .ci-banner strong { color: #0A6E68; }
      .ci-note { color: #506779; font-size: .87rem; }
      .ci-panel-mark { color:#0E7E78; font-size:.71rem; letter-spacing:.11em; font-weight: 750; }
      .ci-audience-track { display:flex; height:27px; border-radius:5px; overflow:hidden; background:#D1DFE8; margin:18px 0 17px; }
      .ci-audience-track span { height:100%; display:block; }
      .ci-audience-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; margin:0 0 12px; }
      .ci-audience-label { font-size:.81rem; color:#5A6D7B; }
      .ci-audience-value { font-weight:750; font-size:1.35rem; color:#142B3B; }
      .ci-dot { display:inline-block; width:8px; height:8px; margin-right:7px; border-radius:2px; }
      .ci-small-note { font-size:.83rem; color:#576E7C; }
      .ci-question-kicker { color:#087F79; font-size:.72rem; letter-spacing:.12em; font-weight:800; border-top:1px solid #D6E6E9; padding-top:13px; margin-top:5px; }
      .ci-question-title {font-weight:760; color:#152C3A; font-size:1rem; padding-top:7px;}
      .ci-check-table { width:100%; border-collapse:separate; border-spacing:0; background:#FFF;
          border:1px solid #D8E5ED; border-radius:8px; overflow:hidden; font-size:.92rem; }
      .ci-check-table th { text-align:left; background:#EAF3F5; color:#173647; font-weight:750;
          padding:12px 14px; border-bottom:1px solid #D8E5ED; }
      .ci-check-table td { padding:12px 14px; border-bottom:1px solid #E4EDF1; vertical-align:top;
          line-height:1.5; color:#213949; }
      .ci-check-table tr:last-child td { border-bottom:0; }
      .ci-check-table th:nth-child(1) { width:28%; }
      .ci-check-table th:nth-child(2) { width:49%; }
      .ci-check-table th:nth-child(3) { width:10%; }
      .ci-check-table th:nth-child(4) { width:13%; }
      .ci-pass { color:#056F63; font-weight:750; }
      .ci-review { color:#B04436; font-weight:750; }
      .ci-check-wrap { overflow-x:auto; margin: 0 0 10px; }
      .ci-check-table { min-width:700px; }
      .st-key-next_campaign_links button { background:transparent !important; color:#087F79 !important;
          border:0 !important; padding:4px 0 !important; font-weight:750 !important;
          box-shadow:none !important; }
      .st-key-next_campaign_links button:hover { color:#064F4B !important; text-decoration:underline !important; }
      section[data-testid="stSidebar"] .st-key-data_guide_btn button {
          background:transparent !important; border:0 !important; color:#79E3CE !important;
          padding-left:0 !important; font-weight:700 !important; }
      section[data-testid="stSidebar"] .st-key-data_guide_btn button:hover { text-decoration:underline !important; }
      @media(max-width:1150px) {
        .ci-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }
      @media(max-width:750px) {
        .ci-topbar-right { gap:7px; font-size:.68rem; }
        .ci-topbar { flex-wrap: wrap; }
        .ci-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px; }
        .ci-kpi-card { min-height: 120px; padding: 13px; }
        .ci-kpi-label { font-size: .94rem; }
        .ci-kpi-number { font-size: 1.65rem; }
        .ci-audience-grid { gap:8px; }
        .ci-audience-value { font-size:1rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data(filename):
    path = DATA_DIR / filename
    return pd.read_csv(path)


required_files = [
    "portfolio_health.csv",
    "channel_performance.csv",
    "monthly_performance_trend.csv",
    "campaign_status.csv",
    "monthly_channel_spend.csv",
    "audience_reconciliation.csv",
]
missing_files = [name for name in required_files if not (DATA_DIR / name).is_file()]
if missing_files:
    st.error("Missing export files: " + ", ".join(missing_files))
    st.info("Keep this file beside app.py and the existing powerbi_exports folder.")
    st.stop()

portfolio = load_data("portfolio_health.csv")
channels = load_data("channel_performance.csv")
monthly = load_data("monthly_performance_trend.csv")
campaign_status = load_data("campaign_status.csv")
monthly_channel = load_data("monthly_channel_spend.csv")
audience = load_data("audience_reconciliation.csv")
segment_file = DATA_DIR / "segment_value_contactability.csv"
segment_values = load_data(segment_file.name) if segment_file.is_file() else None
lift_file = DATA_DIR / "campaign_decision_queue.csv"
lift_data = load_data(lift_file.name) if lift_file.is_file() else None
opportunity_file = DATA_DIR / "customer_opportunity_review.csv"
opportunity_data = load_data(opportunity_file.name) if opportunity_file.is_file() else None

monthly["campaign_month"] = pd.to_datetime(monthly["campaign_month"])
monthly_channel["campaign_month"] = pd.to_datetime(monthly_channel["campaign_month"])
monthly = monthly.sort_values("campaign_month").copy()
monthly_channel = monthly_channel.sort_values(["campaign_month", "channel"]).copy()

p = portfolio.iloc[0]
total_campaigns = int(p["campaigns"])
total_cost = float(p["total_spend"])
tagged_revenue = float(p["campaign_tagged_revenue"])
portfolio_roas = float(p["portfolio_roas"])
meeting_target = int(p["campaigns_meeting_target"])
target_roas = float(p["illustrative_target_roas"])
completed = int((campaign_status["campaign_status"] == "Completed").sum())
other_status = len(campaign_status) - completed
latest_end = pd.to_datetime(campaign_status["end_date"]).max()


def money(value, decimals=0):
    return f"${value:,.{decimals}f}"


def chart_style(fig, height=410):
    fig.update_layout(
        height=height,
        font=dict(family="Arial", size=14, color=NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=25, r=20, t=50, b=35),
        legend=dict(font=dict(size=13)),
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor="#E8EEF3", tickfont=dict(size=12), zeroline=False)
    return fig


# --------------------------------------------------
# Historical conversion comparison (not a causal lift estimate).
# Use campaign_decision_queue.csv, not campaign-tagged revenue or the
# audience funnel's counts, as the source of conversion denominators.
# --------------------------------------------------
COMPARISON_FIELDS = (
    "campaign_id", "treated_n", "treated_conversions",
    "control_n", "control_conversions",
)


def prepare_conversion_records(source):
    """Retain one complete, logically valid treatment/control row per campaign.

    Return (usable_rows, excluded_row_count, duplicate_campaign_count).
    Duplicate campaign IDs are excluded rather than silently double-counted.
    """
    if source is None or not set(COMPARISON_FIELDS).issubset(source.columns):
        return pd.DataFrame(columns=COMPARISON_FIELDS), 0, 0

    df = source.copy()
    for field in COMPARISON_FIELDS:
        df[field] = pd.to_numeric(df[field], errors="coerce")
        df[field] = df[field].replace([float("inf"), -float("inf")], float("nan"))

    duplicates = df["campaign_id"].notna() & df.duplicated("campaign_id", keep=False)
    duplicate_ids = int(df.loc[duplicates, "campaign_id"].nunique())
    numeric = list(COMPARISON_FIELDS)
    valid = (
        df[numeric].notna().all(axis=1)
        & (df["treated_n"] > 0)
        & (df["control_n"] > 0)
        & (df["treated_conversions"] >= 0)
        & (df["control_conversions"] >= 0)
        & (df["treated_conversions"] <= df["treated_n"])
        & (df["control_conversions"] <= df["control_n"])
        & (df[numeric].mod(1) == 0).all(axis=1)
        & ~duplicates
    )
    return df.loc[valid].copy(), int((~valid).sum()), duplicate_ids


def show_conversion_comparison(records, excluded=0, duplicate_ids=0):
    """Show pooled, denominator-weighted historical conversion rates."""
    if records.empty:
        st.info("No complete, valid treatment/holdout conversion counts are available for this selection.")
        return

    treated_n = int(records["treated_n"].sum())
    treated_conversions = int(records["treated_conversions"].sum())
    control_n = int(records["control_n"].sum())
    control_conversions = int(records["control_conversions"].sum())
    treatment_rate = 100 * treated_conversions / treated_n
    control_rate = 100 * control_conversions / control_n
    observed_difference = treatment_rate - control_rate

    a, b, c = st.columns(3)
    a.metric("Recorded-send conversion", f"{treatment_rate:.2f}%")
    b.metric("Holdout conversion", f"{control_rate:.2f}%")
    c.metric("Observed rate difference", f"{observed_difference:+.2f} pp")

    comparison = pd.DataFrame({
        "Group": ["Recorded-send group", "Control holdout"],
        "Conversion rate (%)": [treatment_rate, control_rate],
        "Conversions": [treated_conversions, control_conversions],
        "Customer–campaign records": [treated_n, control_n],
    })
    fig = px.bar(
        comparison, x="Conversion rate (%)", y="Group", color="Group",
        orientation="h", text="Conversion rate (%)",
        custom_data=["Conversions", "Customer–campaign records"],
        color_discrete_map={"Recorded-send group": TEAL, "Control holdout": PURPLE},
    )
    fig.update_traces(
        texttemplate="%{x:.2f}%", textposition="outside", cliponaxis=False,
        hovertemplate=("%{y}<br>Conversion rate: %{x:.2f}%"
                       "<br>Conversions: %{customdata[0]:,.0f}"
                       "<br>Records evaluated: %{customdata[1]:,.0f}<extra></extra>"),
    )
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Conversion rate (%)")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[0, max(treatment_rate, control_rate, 0.1) * 1.28], ticksuffix="%")
    st.plotly_chart(chart_style(fig, 265), width="stretch")
    st.caption(
        f"{treated_conversions:,} conversions / {treated_n:,} recorded-send records; "
        f"{control_conversions:,} / {control_n:,} holdout records. "
        f"Pooled over {len(records):,} campaigns with complete, valid comparison counts. "
        "Rates use summed conversions ÷ summed records, not an average of campaign percentages."
    )
    if excluded:
        st.warning(
            f"{excluded:,} export row(s) were excluded from the comparison because of "
            "missing or invalid counts or duplicate campaign IDs. "
            + (f"{duplicate_ids:,} campaign ID(s) had duplicates. " if duplicate_ids else "")
            + "Review the underlying export before interpreting the pooled figures."
        )
    st.info(
        "The holdout group could purchase without receiving its selected campaign, but may "
        "have received other campaigns. Customers can appear in multiple campaigns. "
        "This is an exploratory, pooled conversion-rate comparison—not an isolated causal "
        "estimate, a pooled confidence interval, or a measure of incremental revenue."
    )


def section(title, subtitle, eyebrow):
    st.markdown(f'<div class="ci-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def navigate_to(destination):
    """Change an existing radio page from a real Streamlit button click."""
    st.session_state["workspace_page"] = destination


@st.dialog("What these numbers mean", width="large")
def show_data_guide():
    st.caption("Methodology, definitions and limitations for this synthetic portfolio.")
    st.markdown("### Source and scope")
    st.write(
        "The Streamlit dashboard reads published CSV exports generated from campaign_analytics.db. "
        "It demonstrates simulated customer and campaign activity, not a real business case. "
        "Monetary values use '$'; the source does not specify a currency. Campaign cost and "
        "audience metrics use campaign start dates. The original companion website's customer "
        "segments use all purchase history through 31 August 2025."
    )
    st.markdown("### Audience and reconciliation")
    st.write(
        "A candidate is one customer considered for one campaign. Counts across campaigns "
        "are customer–campaign records, not unique people. Eligible = recorded sent + control "
        "holdout. Suppressions use the recorded first exclusion reason. 'Sent' is a send record, "
        "not proof of inbox delivery or an ad impression. The original project's send-level "
        "reconciliation compares approved customer–campaign pairs with send records and checks "
        "duplicates; the six checks on this dashboard do not independently rerun that audit."
    )
    st.markdown("### Observed conversion lift")
    st.write(
        "In the original analysis, conversion means at least one order between campaign start "
        "and start + 10 days, inclusive (11 calendar dates), for sent and holdout groups. "
        "Lift is the difference in conversion rates, in percentage points (pp). Campaign "
        "intervals use a 95% Newcombe interval based on Wilson bounds. An exploratory positive "
        "signal requires a lower interval bound above zero and at least 30 holdouts. These are "
        "unadjusted comparisons across many campaigns, not a new experiment run in Streamlit."
    )
    st.write(
        "Customers may appear in several campaigns or receive another campaign while held "
        "out. Sends occur up to three days after campaign start. Therefore observed lift is "
        "not proof of isolated causal impact. Portfolio-wide rates are descriptive pooled "
        "comparisons; no pooled confidence interval is claimed."
    )
    st.markdown("### Attribution and return")
    st.write(
        "In the original companion website, first-touch, last-touch and linear attribution "
        "allocate each order's revenue to recorded campaign sends in the prior 25 days, "
        "inclusive. Same-day first or last touches split credit equally; linear credit is "
        "shared across all eligible sends. These are send-based proxies, not click-based "
        "attribution. Full-journey credit is assigned before campaign filters are applied."
    )
    st.write(
        "Attributed ROAS = attributed revenue ÷ campaign cost. The current Streamlit Overview "
        "uses a DIFFERENT metric: campaign-tagged revenue ÷ recorded campaign cost. Do not "
        "interchange those two revenue figures or ROAS measures. Neither is profit nor "
        "incremental return. A 1.00× ratio recovers campaign cost in revenue before product "
        "costs. Orders with no qualifying send remain unattributed in the original model; "
        "campaign-tagged revenue is not causal ground truth."
    )
    st.markdown("### Customer priorities")
    st.write(
        "The original RFM analysis scores recency, purchase count and monetary value with "
        "NTILE(5), using customer ID as a deterministic tie-break. Higher scores indicate "
        "stronger historical behaviour. Equal values can fall into different tiles. Segment "
        "rules use recency and frequency; monetary value is reported separately. Customers "
        "without purchases appear separately. Segment labels are descriptive, not predicted "
        "future value. Contactability counts are not a substitute for live eligibility checks."
    )
    st.markdown("### Dashboard metric glossary")
    st.markdown(
        "- **Recorded campaign cost:** Cost stored against a campaign. Grouping by launch "
        "month does not show daily cash spending or budget pacing.\n"
        "- **Campaign-tagged revenue:** Revenue linked to a campaign ID in the source data; "
        "not proof the campaign caused the order.\n"
        "- **Tagged orders:** Orders associated with a campaign ID; not necessarily new customers.\n"
        "- **Cost per tagged order:** Recorded campaign cost ÷ tagged orders; not customer "
        "acquisition cost (CAC).\n"
        "- **ROAS:** Revenue ÷ campaign cost. The Overview uses tagged ROAS; the original "
        "attribution page uses attributed ROAS.\n"
        "- **Illustrative target:** A comparison marker of 1.00×; not a profit threshold.\n"
        "- **Completed:** Recorded end date precedes the reporting date, not a verified "
        "delivery or commercial-success status.\n"
        "- **PASS / REVIEW:** A specified validation result under a stated tolerance; "
        "not certification of the entire database.\n"
        "- **Data-quality difference:** Absolute difference between the two quantities "
        "compared; 0.0046 in the unit-cost check is below half a cent of display rounding.\n"
        "- **Recorded-send conversion rate:** Evaluated customer–campaign records with at "
        "least one order in the original 11-calendar-date observation window ÷ evaluated "
        "recorded-send records.\n"
        "- **Holdout conversion rate:** The corresponding rate among records held out of "
        "their selected campaign; not necessarily free of exposure to other campaigns.\n"
        "- **Observed rate difference (pp):** Recorded-send conversion rate minus holdout "
        "conversion rate. This is descriptive when pooled across overlapping campaigns, "
        "not an incremental-revenue estimate."
    )
    st.markdown("### Simulation limitations")
    st.write(
        "The generator applies email consent to non-SMS channels and a shared "
        "contact-frequency limit, with channels processed sequentially. This can affect "
        "channel comparisons. It includes people not yet signed up in candidate pools. "
        "Results demonstrate analytical methods and hypotheses to test, not an instruction "
        "to launch a live campaign or increase spending."
    )
    st.info(
        "Scope distinction: the present Streamlit app shows campaign-tagged outcomes, "
        "CSV-based audience views and aggregate QA; the original companion website also "
        "contains first/last/linear attribution and its own exploratory incrementality "
        "analysis. The new Observed lift page below displays exported estimates, not a "
        "new randomised trial."
    )
    st.link_button("Open original Campaign Intelligence methods ↗",
                   "https://anna-campaign-intelligence.huongzuru.chatgpt.site/")


NAV_PAGES = [
    "01  Overview", "02  Trend", "03  Channel economics",
    "04  Audience & eligibility", "05  Customer priorities",
    "06  Observed lift", "07  Data quality",
]
# Migrate the previous navigation value when this version is first loaded.
if st.session_state.get("workspace_page") == "05  Data quality":
    st.session_state["workspace_page"] = "07  Data quality"


with st.sidebar:
    st.markdown(
        '<div class="ci-side-brand"><span>▥</span> CAMPAIGN INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )
    st.caption("Anna Hoang · SQL + Python + Streamlit")
    st.markdown('<div class="ci-sidebar-rule"></div>', unsafe_allow_html=True)
    st.markdown("**DECISION WORKSPACE**")
    page = st.radio(
        "Decision workspace",
        NAV_PAGES,
        label_visibility="collapsed", key="workspace_page",
    )
    st.markdown('<div class="ci-sidebar-rule"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ci-side-bars" aria-hidden="true"><i></i><i></i><i></i><i></i></div>'
        '<strong>Better questions.<br>Better campaign decisions.</strong>',
        unsafe_allow_html=True,
    )
    st.caption("Python + SQLite · 8,000 synthetic customers · 112 campaigns")
    st.markdown('<div class="ci-sidebar-rule"></div>', unsafe_allow_html=True)
    st.caption("SYNTHETIC PORTFOLIO DATA")
    st.caption("Historical campaign starts: Jan 2024–Jul 2025")
    st.caption("Tagged revenue is not causal incremental revenue.")
    if st.button("How to read the data ↗", key="data_guide_btn", type="tertiary"):
        show_data_guide()

st.markdown(
    '<div class="ci-topbar">'
    '<div class="ci-topbar-left"><span class="ci-topbar-icon">▥</span>'
    '<span><strong>CAMPAIGN</strong> INTELLIGENCE</span></div>'
    '<div class="ci-topbar-right"><span class="ci-synth">SYNTHETIC DATA</span>'
    '<span>Anna Hoang · SQL portfolio</span></div></div>',
    unsafe_allow_html=True,
)

if page == "01  Overview":
    section(
        "Where should the next dollar go?",
        "Balance campaign return with audience quality and evidence of additional purchases.",
        "The business view",
    )
    st.caption("All 112 campaigns · Historical portfolio · Synthetic data · Campaign starts Jan 2024–Jul 2025")
    if st.button("How to read the data ↗", key="overview_data_guide", type="tertiary"):
        show_data_guide()
    st.markdown(
        '<div class="ci-kpi-grid">'
        f'<div class="ci-kpi-card"><div class="ci-kpi-label">Campaigns</div>'
        f'<div class="ci-kpi-number">{total_campaigns:,}</div></div>'
        f'<div class="ci-kpi-card"><div class="ci-kpi-label">Recorded campaign cost</div>'
        f'<div class="ci-kpi-number">{money(total_cost)}</div></div>'
        f'<div class="ci-kpi-card"><div class="ci-kpi-label">Campaign-tagged revenue</div>'
        f'<div class="ci-kpi-number">{money(tagged_revenue)}</div></div>'
        f'<div class="ci-kpi-card"><div class="ci-kpi-label">Portfolio tagged ROAS</div>'
        f'<div class="ci-kpi-number">{portfolio_roas:.2f}×</div></div>'
        f'<div class="ci-kpi-card"><div class="ci-kpi-label">Meeting illustrative target</div>'
        f'<div class="ci-kpi-number">{meeting_target / total_campaigns:.1%}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="ci-banner"><strong>CAMPAIGN LIFECYCLE · </strong> '
        f'{completed} of {len(campaign_status)} completed as of {REPORT_DATE}; '
        f'{other_status} in progress or scheduled. Latest recorded end: {latest_end:%d %b %Y}.'
        '</div>', unsafe_allow_html=True,
    )

    top = channels.sort_values("roas", ascending=False).iloc[0]
    st.markdown(
        '<div class="ci-banner"><strong>DECISION NOTE · </strong>'
        f'{top["channel"]} has {float(top["roas"]):.2f}× campaign-tagged ROAS in this historical portfolio. '
        'This is an observed tagged return, not evidence of incremental impact; '
        'use eligibility and controlled-test evidence before committing new spend.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="ci-panel-mark">CHANNEL PERFORMANCE</div>', unsafe_allow_html=True)
            st.subheader("Which channel delivers the highest campaign-tagged ROAS?")
            roas_view = channels.sort_values("roas", ascending=True)
            fig = px.bar(
                roas_view, x="roas", y="channel", color="channel", orientation="h",
                text="roas", color_discrete_map=CHANNEL_COLORS,
                labels={"roas": "Campaign-tagged ROAS", "channel": ""},
            )
            fig.update_traces(texttemplate="%{text:.2f}×", textposition="outside", cliponaxis=False)
            fig.add_vline(x=target_roas, line_dash="dash", line_color="#788C9A")
            fig.update_layout(showlegend=False, xaxis_range=[0, max(1.1, float(channels["roas"].max()) * 1.20)])
            st.plotly_chart(chart_style(fig, 330), width="stretch")
            st.caption("Dashed line = illustrative 1.00× target; not a profitability threshold.")

    with right:
        with st.container(border=True):
            st.markdown('<div class="ci-panel-mark">UNIT ECONOMICS</div>', unsafe_allow_html=True)
            st.subheader("Cost per tagged order by channel")
            cpo = channels[["channel", "campaign_orders", "spend", "cost_per_order"]].copy()
            cpo = cpo.sort_values("cost_per_order")
            cpo = cpo.rename(columns={
                "channel": "Channel", "campaign_orders": "Tagged orders",
                "spend": "Campaign cost", "cost_per_order": "Cost / tagged order",
            })
            fig = px.bar(
                cpo.sort_values("Cost / tagged order", ascending=False),
                x="Cost / tagged order", y="Channel", color="Channel", orientation="h",
                text="Cost / tagged order", color_discrete_map=CHANNEL_COLORS,
                custom_data=["Tagged orders", "Campaign cost"],
            )
            fig.update_traces(
                texttemplate="$%{text:,.2f}", textposition="outside", cliponaxis=False,
                hovertemplate="Cost / tagged order: $%{x:,.2f}<br>Tagged orders: %{customdata[0]:,.0f}<br>Campaign cost: $%{customdata[1]:,.0f}<extra></extra>",
            )
            fig.update_layout(showlegend=False, xaxis_title="Cost per tagged order ($)", yaxis_title="")
            fig.update_xaxes(tickprefix="$", tickformat=",.0f", range=[0, float(cpo["Cost / tagged order"].max()) * 1.25])
            st.plotly_chart(chart_style(fig, 330), width="stretch")
            with st.expander("View exact cost-per-order figures"):
                st.dataframe(
                    cpo, hide_index=True, width="stretch",
                    column_config={
                        "Tagged orders": st.column_config.NumberColumn(format="%d"),
                        "Campaign cost": st.column_config.NumberColumn(format="$%.0f"),
                        "Cost / tagged order": st.column_config.NumberColumn(format="$%.2f"),
                    },
                )
            st.caption("Campaign cost ÷ tagged orders; not customer acquisition cost or proven incremental purchases.")

    # Audience and next-campaign questions follow the channel comparison,
    # before the portfolio-wide campaign cost / tagged revenue chart.
    cand = int(pd.to_numeric(audience["candidate_pool"], errors="coerce").fillna(0).sum())
    sent = int(pd.to_numeric(audience["sent"], errors="coerce").fillna(0).sum())
    holdout = int(pd.to_numeric(audience["control_holdout"], errors="coerce").fillna(0).sum())
    suppressed = int(pd.to_numeric(audience["suppressed_total"], errors="coerce").fillna(0).sum())
    audience_total = sent + holdout + suppressed
    pct_sent = 100 * sent / cand if cand else 0
    pct_holdout = 100 * holdout / cand if cand else 0
    pct_suppressed = 100 * suppressed / cand if cand else 0
    suppressed_reasons = {
        "Not yet signed up": "supp_not_yet_signed_up",
        "Contact-frequency cap": "supp_frequency_cap",
        "No channel consent": "supp_no_consent",
        "Opted out": "supp_opted_out",
        "Recent purchase": "supp_recent_purchase",
    }
    reason_totals = {label: int(pd.to_numeric(audience[field], errors="coerce").fillna(0).sum())
                     for label, field in suppressed_reasons.items()}
    largest_reason, largest_count = max(reason_totals.items(), key=lambda item: item[1])
    reason_pct = 100 * largest_count / suppressed if suppressed else 0

    with st.container(border=True):
        st.markdown('<div class="ci-panel-mark">BEFORE THE SEND</div>', unsafe_allow_html=True)
        st.subheader("How much of the audience can we reach?")
        st.caption(f"{cand:,} candidate records considered across the selected historical portfolio")
        st.markdown(
            '<div class="ci-audience-track" role="img" aria-label="Candidate audience breakdown">'
            f'<span style="width:{pct_sent:.5f}%;background:#087F79" title="Recorded sent"></span>'
            f'<span style="width:{pct_holdout:.5f}%;background:#7C62B3" title="Control holdout"></span>'
            f'<span style="width:{pct_suppressed:.5f}%;background:#CDDCE5" title="Suppressed"></span>'
            '</div>'
            '<div class="ci-audience-grid">'
            f'<div><div class="ci-audience-label"><i class="ci-dot" style="background:#087F79"></i>Recorded sent</div><div class="ci-audience-value">{sent:,}</div><div class="ci-small-note">{pct_sent:.1f}% of candidates</div></div>'
            f'<div><div class="ci-audience-label"><i class="ci-dot" style="background:#7C62B3"></i>Control holdout</div><div class="ci-audience-value">{holdout:,}</div><div class="ci-small-note">{pct_holdout:.1f}% of candidates</div></div>'
            f'<div><div class="ci-audience-label"><i class="ci-dot" style="background:#91A9B8"></i>Suppressed</div><div class="ci-audience-value">{suppressed:,}</div><div class="ci-small-note">{pct_suppressed:.1f}% of candidates</div></div>'
            '</div>', unsafe_allow_html=True,
        )
        st.caption("Eligible = recorded sent + holdout. A send record does not confirm delivery; repeated customers count once per campaign.")
        if cand != audience_total:
            st.warning(f"Audience totals do not reconcile: candidates {cand:,}; outcomes {audience_total:,}.")
        st.button("Review audience →", key="overview_audience_link", type="tertiary",
                  on_click=navigate_to, args=("04  Audience & eligibility",))

    st.markdown(" ")
    with st.container(border=True):
        st.markdown('<div class="ci-panel-mark">CAMPAIGN EFFECTIVENESS</div>', unsafe_allow_html=True)
        st.subheader("Would customers have purchased without this campaign?")
        st.caption(
            "Historical 11-calendar-date conversion comparison: recorded-send group versus "
            "the group held out from its selected campaign."
        )
        if lift_data is None:
            st.info("Add campaign_decision_queue.csv to powerbi_exports to see the observed conversion comparison.")
        else:
            overview_records, overview_excluded, overview_duplicates = prepare_conversion_records(lift_data)
            show_conversion_comparison(overview_records, overview_excluded, overview_duplicates)
            st.button("Explore campaign-level lift and uncertainty →", key="overview_conversion_link",
                      type="tertiary", on_click=navigate_to, args=("06  Observed lift",))

    st.markdown(" ")
    with st.container(border=True):
        st.subheader("Three questions for the next campaign")
        st.caption("Turn this historical analysis into a testable plan.")
        q1, q2, q3 = st.columns(3, gap="large")
        with q1:
            st.markdown('<div class="ci-question-kicker">01 / AUDIENCE QUALITY</div>', unsafe_allow_html=True)
            st.markdown('<div class="ci-question-title">Resolve exclusions first</div>', unsafe_allow_html=True)
            st.write(f"{pct_suppressed:.1f}% of candidate records were suppressed. The largest recorded reason is {largest_reason.lower()} ({largest_count:,}; {reason_pct:.1f}% of suppressions). Review eligibility before expanding sends.")
        with q2:
            st.markdown('<div class="ci-question-kicker">02 / CUSTOMER PRIORITY</div>', unsafe_allow_html=True)
            st.markdown('<div class="ci-question-title">Test a focused win-back offer</div>', unsafe_allow_html=True)
            at_risk_summary = "Use the at-risk frequent-buyer segment as a test hypothesis; refresh eligibility before contacting anyone."
            if segment_values is not None and {"segment", "customers", "revenue_share_pct"}.issubset(segment_values.columns):
                matched = segment_values[segment_values["segment"].astype(str).str.casefold().str.contains("at-risk frequent", regex=False)]
                if not matched.empty:
                    item = matched.iloc[0]
                    share = float(item["revenue_share_pct"])
                    share = share * 100 if 0 <= share <= 1 else share
                    at_risk_summary = f"{int(item['customers']):,} at-risk frequent buyers represent {share:.1f}% of historical revenue. Refresh eligibility before a controlled win-back test."
            st.write(at_risk_summary)
        with q3:
            st.markdown('<div class="ci-question-kicker">03 / ADDITIONAL PURCHASES</div>', unsafe_allow_html=True)
            st.markdown('<div class="ci-question-title">Look beyond credited sales</div>', unsafe_allow_html=True)
            st.write("Compare sent and holdout conversion rates, sample sizes and uncertainty before treating tagged sales as evidence of additional purchases.")
        # A separate row ensures the three links share the same baseline, even if
        # question descriptions wrap onto different numbers of lines.
        with st.container(key="next_campaign_links"):
            link1, link2, link3 = st.columns(3, gap="large")
            with link1:
                st.button("Review audience →", key="next_audience", type="tertiary",
                          on_click=navigate_to, args=("04  Audience & eligibility",))
            with link2:
                st.button("Explore customer priorities →", key="next_customer", type="tertiary",
                          on_click=navigate_to, args=("05  Customer priorities",))
            with link3:
                st.button("Examine observed lift →", key="next_lift", type="tertiary",
                          on_click=navigate_to, args=("06  Observed lift",))

    with st.container(border=True):
        st.markdown('<div class="ci-panel-mark">PORTFOLIO FINANCIALS</div>', unsafe_allow_html=True)
        st.subheader("Campaign cost versus campaign-tagged revenue")
        finance = channels.melt(
            id_vars="channel", value_vars=["spend", "campaign_tagged_revenue"],
            var_name="Metric", value_name="Amount",
        )
        finance["Metric"] = finance["Metric"].replace(
            {"spend": "Recorded cost", "campaign_tagged_revenue": "Tagged revenue"}
        )
        fig = px.bar(
            finance, x="channel", y="Amount", color="Metric", barmode="group",
            color_discrete_map={"Recorded cost": NAVY, "Tagged revenue": TEAL},
            labels={"channel": "Channel", "Amount": "Amount ($; currency unspecified)"},
        )
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        fig.update_layout(legend=dict(orientation="h", y=1.09, x=0))
        st.plotly_chart(chart_style(fig, 400), width="stretch")
        st.caption("Historical campaign cost and tagged revenue. This is not an incremental-profit calculation.")

elif page == "02  Trend":
    section(
        "How has performance changed over time?",
        "Compare channel costs in each launch month, total campaign cost and campaign-tagged ROAS.",
        "Performance trend",
    )
    year_choice = st.selectbox("Chart period", ["All months", "2024", "2025"])
    shown_months = monthly.copy()
    shown_channel = monthly_channel.copy()
    if year_choice != "All months":
        shown_months = shown_months[shown_months["campaign_month"].dt.year == int(year_choice)]
        shown_channel = shown_channel[shown_channel["campaign_month"].dt.year == int(year_choice)]

    changes = shown_months["roas"].diff().dropna()
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Months shown", f"{len(shown_months)}")
    t2.metric("ROAS improved vs prior month", str(int((changes > 0).sum())))
    t3.metric("ROAS declined vs prior month", str(int((changes < 0).sum())))
    t4.metric("Latest month ROAS", f"{float(shown_months.iloc[-1]['roas']):.2f}×")
    st.caption("Month-on-month counts compare only months within the selected chart period.")

    st.subheader("Monthly campaign cost by channel")
    pivot = shown_channel.pivot_table(
        index="campaign_month", columns="channel", values="spend", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    for channel in CHANNEL_ORDER:
        if channel in pivot.columns:
            fig.add_trace(go.Bar(
                x=pivot.index, y=pivot[channel], name=channel,
                marker_color=CHANNEL_COLORS[channel],
                hovertemplate=f"{channel}: $%{{y:,.0f}}<extra></extra>",
            ))
    fig.add_trace(go.Scatter(
        x=pivot.index, y=pivot.sum(axis=1), name="Total campaign cost",
        mode="lines+markers", line=dict(color=NAVY, width=3),
        marker=dict(size=8, color=NAVY),
        hovertemplate="Total campaign cost: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        barmode="group", bargap=.22, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
    )
    fig.update_xaxes(tickformat="%b\n%Y", dtick="M2", title="Campaign start month")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", title="Recorded campaign cost ($)")
    st.plotly_chart(chart_style(fig, 530), width="stretch")
    st.caption(
        "Bars show cost recorded against each campaign's start month; the dark line is the "
        "sum of the four channel bars. This is not daily cash-spend or budget pacing."
    )

    st.subheader("Monthly campaign-tagged ROAS")
    fig = px.line(
        shown_months, x="campaign_month", y="roas", markers=True,
        labels={"campaign_month": "Campaign start month", "roas": "Tagged ROAS"},
    )
    fig.update_traces(line_color=TEAL, line_width=3, marker_size=8)
    fig.add_hline(
        y=target_roas, line_dash="dash", line_color=ORANGE,
        annotation_text=f"Illustrative target {target_roas:.2f}×",
        annotation_position="top left",
    )
    fig.update_xaxes(tickformat="%b %Y", dtick="M2")
    fig.update_yaxes(ticksuffix="×")
    st.plotly_chart(chart_style(fig, 400), width="stretch")

    with st.expander("View underlying monthly figures"):
        st.dataframe(shown_months, hide_index=True, width="stretch")
        st.dataframe(shown_channel, hide_index=True, width="stretch")

elif page == "03  Channel economics":
    section(
        "Which channels earn their recorded cost?",
        "Filter the channel view; portfolio-wide KPI figures remain unchanged on the Overview page.",
        "Channel economics",
    )
    selected = st.selectbox("Marketing channel", ["All channels"] + CHANNEL_ORDER)
    view = channels if selected == "All channels" else channels[channels["channel"] == selected]
    v1, v2, v3 = st.columns(3)
    v1.metric("Campaign cost in view", money(float(view["spend"].sum())))
    v2.metric("Tagged orders in view", f"{int(view['campaign_orders'].sum()):,}")
    v3.metric(
        "Weighted cost / tagged order",
        money(float(view["spend"].sum()) / float(view["campaign_orders"].sum()), 2)
        if view["campaign_orders"].sum() else "N/A",
    )
    st.subheader("Channel cost versus tagged revenue")
    finance_view = view.melt(
        id_vars="channel", value_vars=["spend", "campaign_tagged_revenue"],
        var_name="Metric", value_name="Amount",
    )
    finance_view["Metric"] = finance_view["Metric"].replace({
        "spend": "Recorded cost", "campaign_tagged_revenue": "Tagged revenue",
    })
    fig = px.bar(
        finance_view, x="channel", y="Amount", color="Metric", barmode="group",
        color_discrete_map={"Recorded cost": NAVY, "Tagged revenue": TEAL},
        labels={"channel": "Channel", "Amount": "Amount ($; currency unspecified)"},
    )
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(chart_style(fig, 390), width="stretch")

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Tagged ROAS by channel")
        fig = px.bar(
            view.sort_values("roas"), x="roas", y="channel", color="channel",
            orientation="h", text="roas", color_discrete_map=CHANNEL_COLORS,
            labels={"roas": "Tagged ROAS", "channel": ""},
        )
        fig.update_traces(texttemplate="%{text:.2f}×", textposition="outside", cliponaxis=False)
        fig.add_vline(x=target_roas, line_dash="dash", line_color="#788C9A")
        fig.update_layout(showlegend=False)
        fig.update_xaxes(range=[0, max(1.1, float(channels["roas"].max()) * 1.2)])
        st.plotly_chart(chart_style(fig, 330), width="stretch")
    with right:
        st.subheader("Cost per tagged order")
        cpo_view = view.sort_values("cost_per_order", ascending=False)
        fig = px.bar(
            cpo_view, x="cost_per_order", y="channel", color="channel",
            orientation="h", text="cost_per_order", color_discrete_map=CHANNEL_COLORS,
            labels={"cost_per_order": "Cost per tagged order ($)", "channel": ""},
        )
        fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(tickprefix="$", range=[0, float(channels["cost_per_order"].max()) * 1.25])
        st.plotly_chart(chart_style(fig, 330), width="stretch")

    with st.expander("View exact channel financials"):
        cols = ["channel", "campaigns_run", "spend", "campaign_orders", "campaign_tagged_revenue", "roas", "cost_per_order"]
        st.dataframe(view[cols], hide_index=True, width="stretch")
    st.caption("The combined ROAS and cost-per-order figures use summed numerators and denominators, not averages of channel ratios.")

elif page == "04  Audience & eligibility":
    section(
        "Who should receive the campaign?",
        "Trace candidate selection, eligible audiences and recorded exclusion reasons.",
        "Audience operations",
    )

    # The export is campaign-grain: a customer can be counted in multiple campaigns.
    a = audience.copy()
    status_lookup = campaign_status[["campaign_id", "campaign_name", "channel"]].copy()
    status_lookup["campaign_id"] = pd.to_numeric(status_lookup["campaign_id"], errors="coerce")
    status_lookup = status_lookup.drop_duplicates(subset=["campaign_id"])
    a["campaign_id"] = pd.to_numeric(a["campaign_id"], errors="coerce")
    a = a.merge(status_lookup, on="campaign_id", how="left", validate="many_to_one")

    count_fields = [
        "candidate_pool", "sent", "control_holdout", "suppressed_total",
        "reconciliation_gap", "supp_no_consent", "supp_opted_out",
        "supp_frequency_cap", "supp_recent_purchase", "supp_not_yet_signed_up",
    ]
    for field in count_fields:
        a[field] = pd.to_numeric(a[field], errors="coerce").fillna(0)

    channel_choices = ["All channels"] + sorted(a["channel"].dropna().unique().tolist())
    ac1, ac2 = st.columns([1, 2])
    with ac1:
        audience_channel = st.selectbox("Channel", channel_choices, key="audience_channel")
    view = a if audience_channel == "All channels" else a[a["channel"] == audience_channel]
    names = view.sort_values("campaign_id")[["campaign_id", "campaign_name"]].drop_duplicates()
    campaign_choices = {"All campaigns": None}
    for item in names.itertuples(index=False):
        name = str(item.campaign_name) if pd.notna(item.campaign_name) else "Unnamed campaign"
        campaign_choices[f"#{int(item.campaign_id)} · {name}"] = item.campaign_id
    with ac2:
        campaign_label = st.selectbox("Campaign", list(campaign_choices), key="audience_campaign")
    chosen_id = campaign_choices[campaign_label]
    if chosen_id is not None:
        view = view[view["campaign_id"] == chosen_id]

    candidate_count = int(view["candidate_pool"].sum())
    sent_count = int(view["sent"].sum())
    holdout_count = int(view["control_holdout"].sum())
    suppressed_count = int(view["suppressed_total"].sum())
    eligible_count = sent_count + holdout_count
    suppressed_pct = suppressed_count / candidate_count if candidate_count else 0
    computed_gap = view["candidate_pool"] - (
        view["sent"] + view["control_holdout"] + view["suppressed_total"]
    )
    reason_fields = {
        "Not yet signed up": "supp_not_yet_signed_up",
        "Contact-frequency cap": "supp_frequency_cap",
        "No channel consent": "supp_no_consent",
        "Opted out": "supp_opted_out",
        "Recent purchase": "supp_recent_purchase",
    }
    reason_sum = view[list(reason_fields.values())].sum(axis=1)
    reason_gap = view["suppressed_total"] - reason_sum
    mismatched_rows = int((computed_gap != 0).sum())
    reason_mismatches = int((reason_gap != 0).sum())
    recorded_gap_rows = int((view["reconciliation_gap"] != 0).sum())

    st.caption(
        f"{len(view):,} campaigns in view · Counts are customer–campaign records, "
        "not unique people across campaigns."
    )
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Candidate records", f"{candidate_count:,}")
    v2.metric("Eligible (sent + holdout)", f"{eligible_count:,}")
    v3.metric("Suppressed", f"{suppressed_count:,}", f"{suppressed_pct:.1%} of candidates", delta_color="off")
    v4.metric("Candidate reconciliation gaps", f"{mismatched_rows:,}")

    st.markdown('<div class="ci-banner"><strong>Before the send:</strong> '
                f'{candidate_count:,} candidates = {sent_count:,} recorded sent + '
                f'{holdout_count:,} control holdouts + {suppressed_count:,} suppressed. '
                'A send record does not by itself confirm delivery.</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1.1], gap="large")
    with left:
        st.subheader("Where did the candidate pool go?")
        statuses = pd.DataFrame({
            "Outcome": ["Recorded sent", "Control holdout", "Suppressed"],
            "Records": [sent_count, holdout_count, suppressed_count],
        })
        status_colors = {"Recorded sent": TEAL, "Control holdout": PURPLE, "Suppressed": "#C9D8E2"}
        fig = px.bar(
            statuses, x="Records", y=["Candidate pool"] * 3, color="Outcome",
            orientation="h", color_discrete_map=status_colors,
            custom_data=["Records"],
        )
        fig.update_traces(hovertemplate="%{fullData.name}: %{x:,.0f} records<extra></extra>")
        fig.update_layout(
            barmode="stack", xaxis_title="Candidate records", yaxis_title="",
            legend=dict(orientation="h", y=1.3, x=0),
        )
        st.plotly_chart(chart_style(fig, 245), width="stretch")
        for col, label, n in zip(st.columns(3), ["Recorded sent", "Control holdout", "Suppressed"],
                                 [sent_count, holdout_count, suppressed_count]):
            col.metric(label, f"{n:,}")
        st.caption("Eligible = recorded sent + holdout; these are selection outcomes, not confirmed deliveries.")

    with right:
        st.subheader("Why were records excluded?")
        reason_data = pd.DataFrame({
            "Reason": list(reason_fields),
            "Records": [int(view[field].sum()) for field in reason_fields.values()],
        }).sort_values("Records", ascending=True)
        fig = px.bar(
            reason_data, x="Records", y="Reason", orientation="h", text="Records",
            color="Reason", color_discrete_sequence=["#6B8799", ORANGE, BLUE, PURPLE, TEAL],
        )
        fig.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False, xaxis_title="Suppressed records", yaxis_title="")
        st.plotly_chart(chart_style(fig, 345), width="stretch")
        st.caption("Uses the recorded primary suppression reason. Each suppressed record should appear once.")

    st.subheader("Campaign audience audit")
    audit = view[[
        "campaign_id", "campaign_name", "channel", "candidate_pool", "sent",
        "control_holdout", "suppressed_total", "reconciliation_gap",
    ]].copy()
    audit["Calculated candidate gap"] = computed_gap.loc[audit.index]
    audit["Suppression-reason gap"] = reason_gap.loc[audit.index]
    audit = audit.rename(columns={
        "campaign_id": "Campaign ID", "campaign_name": "Campaign", "channel": "Channel",
        "candidate_pool": "Candidates", "sent": "Recorded sent", "control_holdout": "Holdout",
        "suppressed_total": "Suppressed", "reconciliation_gap": "Exported reconciliation gap",
    }).sort_values("Campaign ID")
    st.dataframe(audit, hide_index=True, width="stretch")
    st.download_button(
        "Download audience audit CSV", audit.to_csv(index=False).encode("utf-8"),
        file_name="audience_audit_filtered.csv", mime="text/csv",
    )
    if mismatched_rows == 0 and reason_mismatches == 0 and recorded_gap_rows == 0:
        st.success("Candidate totals, recorded suppression reasons and exported reconciliation gaps agree for this selection.")
    else:
        st.warning(
            f"Review {mismatched_rows} candidate-sum gaps, {reason_mismatches} suppression-reason gaps "
            f"and {recorded_gap_rows} non-zero exported reconciliation gaps."
        )
    st.caption(
        "These checks do not verify that every recorded send matches its audience selection, "
        "nor do they establish consent compliance at send time."
    )

elif page == "05  Customer priorities":
    section(
        "Who should we nurture or win back?",
        "Understand historical customer value before proposing a new audience or contact strategy.",
        "Customer priorities",
    )
    st.info("Historical segments are hypotheses for future tests, not an approved send list. Refresh consent, eligibility and contact history before activation.")
    if segment_values is None:
        st.warning("The segment_value_contactability.csv export is not available. Add it to powerbi_exports to view this page.")
    else:
        sv = segment_values.copy()
        number_fields = ["customers", "segment_revenue", "revenue_share_pct", "customer_share_pct",
                         "email_contactable_customers", "sms_contactable_customers"]
        for field in number_fields:
            if field in sv.columns:
                sv[field] = pd.to_numeric(sv[field], errors="coerce").fillna(0)
        for field in ("customer_share_pct", "revenue_share_pct"):
            if field in sv.columns and sv[field].abs().max() <= 1.0001:
                sv[field] = sv[field] * 100
        c1, c2, c3 = st.columns(3)
        c1.metric("Segmented historical buyers", f"{int(sv['customers'].sum()):,}")
        c2.metric("Historical segment revenue", money(float(sv['segment_revenue'].sum())))
        c3.metric("Segments", f"{len(sv)}")
        st.caption("Only customers in exported segments are counted above; this does not necessarily equal the entire customer base.")
        share = sv.melt(id_vars="segment", value_vars=["customer_share_pct", "revenue_share_pct"],
                        var_name="Measure", value_name="Percent")
        share["Measure"] = share["Measure"].replace({
            "customer_share_pct": "Share of buyers", "revenue_share_pct": "Share of historical revenue"})
        fig = px.bar(share, y="segment", x="Percent", color="Measure", barmode="group",
                     orientation="h", color_discrete_map={"Share of buyers": "#A8BFCD",
                                                                "Share of historical revenue": TEAL},
                     labels={"segment": "Segment", "Percent": "Share (%)"})
        fig.update_xaxes(ticksuffix="%")
        st.subheader("Customer share versus historical revenue share")
        st.plotly_chart(chart_style(fig, 420), width="stretch")
        cols = [c for c in ["segment", "customers", "segment_revenue", "customer_share_pct",
                            "revenue_share_pct", "email_contactable_customers", "sms_contactable_customers"]
                if c in sv.columns]
        st.subheader("Segment contactability summary")
        st.dataframe(sv[cols], hide_index=True, width="stretch")
        st.caption("Contactability counts are a historical indicator, not final approval to contact a customer.")
        if opportunity_data is not None:
            with st.expander("Review synthetic customer opportunities"):
                st.dataframe(opportunity_data, hide_index=True, width="stretch")

elif page == "06  Observed lift":
    section(
        "Would customers have purchased without this campaign?",
        "Compare historical recorded-send and holdout conversion rates, then inspect uncertainty.",
        "Campaign effectiveness",
    )
    st.warning("This page reads precomputed historical estimates, not the result of a new randomised Email reallocation test. Overlapping campaign exposure and unadjusted comparisons limit causal interpretation.")
    if lift_data is None:
        st.warning("The campaign_decision_queue.csv export is not available. Add it to powerbi_exports to view this page.")
    else:
        lv = lift_data.copy()
        selected_lift_channel = st.selectbox(
            "Channel", ["All channels"] + sorted(lv["channel"].dropna().unique().tolist()),
            key="lift_filter_channel",
        )
        if selected_lift_channel != "All channels":
            lv = lv[lv["channel"] == selected_lift_channel].copy()

        with st.container(border=True):
            st.markdown('<div class="ci-panel-mark">OBSERVED CONVERSION COMPARISON</div>',
                        unsafe_allow_html=True)
            st.subheader("Would customers have purchased without this campaign?")
            records, excluded_rows, duplicate_ids = prepare_conversion_records(lv)
            show_conversion_comparison(records, excluded_rows, duplicate_ids)

        numeric_fields = ["estimated_lift_pp", "lift_ci_lower_pp", "lift_ci_upper_pp", "treated_n",
                          "treated_conversions", "control_n", "control_conversions"]
        for field in numeric_fields:
            lv[field] = pd.to_numeric(lv[field], errors="coerce")
        available = lv.dropna(subset=["estimated_lift_pp", "lift_ci_lower_pp", "lift_ci_upper_pp", "control_n"]).copy()
        available["Signal"] = available.apply(
            lambda r: "Exploratory positive signal" if r["control_n"] >= 30 and r["lift_ci_lower_pp"] > 0
            else "Inconclusive / review", axis=1)
        m1, m2, m3 = st.columns(3)
        m1.metric("Campaigns in selection", f"{len(lv):,}")
        m2.metric("Estimates with intervals", f"{len(available):,}")
        m3.metric("Exploratory positive signals",
                  f"{int((available['Signal'] == 'Exploratory positive signal').sum()):,}")
        st.subheader("Estimated conversion-rate difference and 95% interval")
        st.caption("Percentage points (pp). The interval crossing zero is not evidence of a positive difference at this exploratory threshold.")
        display = available.sort_values("estimated_lift_pp", ascending=False).head(12).copy()
        if display.empty:
            st.info("No comparable campaign estimates for the selected channel.")
        else:
            display = display.sort_values("estimated_lift_pp", ascending=True)
            fig = go.Figure()
            for row in display.itertuples(index=False):
                label = f"#{int(row.campaign_id)} · {row.channel}"
                lower, middle, upper = float(row.lift_ci_lower_pp), float(row.estimated_lift_pp), float(row.lift_ci_upper_pp)
                color = TEAL if row.Signal == "Exploratory positive signal" else "#8199AA"
                fig.add_trace(go.Scatter(
                    x=[lower, upper], y=[label, label], mode="lines", line=dict(color=color, width=4),
                    showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(
                    x=[middle], y=[label], mode="markers", marker=dict(color=color, size=10),
                    showlegend=False, hovertemplate=f"{label}<br>Estimated lift: {middle:+.2f} pp<br>95% interval: [{lower:.2f}, {upper:.2f}] pp<extra></extra>"))
            fig.add_vline(x=0, line_dash="dash", line_color="#8499A8")
            fig.update_layout(xaxis_title="Observed conversion-rate difference (pp)", yaxis_title="",
                              margin=dict(l=130, r=20, t=35, b=45))
            st.plotly_chart(chart_style(fig, max(360, len(display)*35)), width="stretch")
        st.subheader("Campaign-level evidence")
        evidence_cols = ["campaign_id", "campaign_name", "channel", "treated_n", "treated_conversions",
                         "control_n", "control_conversions", "estimated_lift_pp", "lift_ci_lower_pp",
                         "lift_ci_upper_pp", "Signal"]
        st.dataframe(available[evidence_cols], hide_index=True, width="stretch")
        st.caption("A lower interval bound above zero with at least 30 holdouts is an exploratory signal—not proof of isolated causal impact. This is not a new or prospective controlled test.")

elif page == "07  Data quality":
    section(
        "Do the reported totals reconcile?",
        "Aggregate reconciliation checks across the currently loaded exports.",
        "Data quality",
    )
    def check_row(name, explanation, observed, expected, tolerance=.10):
        gap = abs(float(observed) - float(expected))
        return {
            "Check": name, "Plain-English explanation": explanation,
            "Status": "PASS" if gap <= tolerance else "REVIEW", "Difference": gap,
        }

    checks = [
        check_row("Campaign count: status file vs portfolio",
                  "Does the number of campaigns in the campaign-status export match the portfolio total of 112?",
                  len(campaign_status), total_campaigns, 0),
        check_row("Campaign cost: status file vs portfolio",
                  "Does adding up individual campaign costs produce the same total as the portfolio KPI?",
                  campaign_status["cost"].sum(), total_cost),
        check_row("Channel cost vs portfolio",
                  "Does the combined cost of Email, SMS, Paid Social and Display equal the portfolio cost?",
                  channels["spend"].sum(), total_cost),
        check_row("Monthly cost vs portfolio",
                  "Does adding up all monthly campaign costs equal the portfolio cost?",
                  monthly["spend"].sum(), total_cost),
        check_row("Month-channel cost vs monthly report",
                  "Does the sum of channel costs within each month agree with that month's reported total?",
                  monthly_channel["spend"].sum(), monthly["spend"].sum()),
    ]
    order_rows = channels[channels["campaign_orders"] > 0]
    if not order_rows.empty:
        calculated = order_rows["spend"] / order_rows["campaign_orders"]
        checks.append(check_row(
            "Cost / tagged order: largest channel-level rounding gap",
            "Does the displayed cost-per-order figure agree with cost divided by tagged orders, allowing for rounding?",
            (calculated - order_rows["cost_per_order"]).abs().max(), 0, .005,
        ))
    quality = pd.DataFrame(checks)
    q1, q2, q3 = st.columns(3)
    q1.metric("Checks run", len(quality))
    q2.metric("Passed", int((quality["Status"] == "PASS").sum()))
    q3.metric("Flagged for review", int((quality["Status"] != "PASS").sum()))
    st.subheader("Reconciliation check results")
    status_counts = quality["Status"].value_counts().reindex(["PASS", "REVIEW"], fill_value=0).reset_index()
    status_counts.columns = ["Status", "Checks"]
    fig = px.bar(
        status_counts, x="Status", y="Checks", color="Status", text="Checks",
        color_discrete_map={"PASS": TEAL, "REVIEW": "#B94A37"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Number of checks")
    fig.update_yaxes(dtick=1, range=[0, max(1, len(quality)) + 1])
    st.plotly_chart(chart_style(fig, 285), width="stretch")
    st.subheader("Check-by-check evidence")
    row_html = "".join(
        "<tr>"
        f"<td>{escape(str(row['Check']))}</td>"
        f"<td>{escape(str(row['Plain-English explanation']))}</td>"
        f"<td><span class={'ci-pass' if row['Status'] == 'PASS' else 'ci-review'}>"
        f"{escape(str(row['Status']))}</span></td>"
        f"<td style='text-align:right;font-variant-numeric:tabular-nums'>"
        f"{float(row['Difference']):.4f}</td>"
        "</tr>"
        for _, row in quality.iterrows()
    )
    st.markdown(
        '<div class="ci-check-wrap"><table class="ci-check-table">'
        '<thead><tr><th>Check</th><th>Plain-English explanation</th>'
        '<th>Result</th><th>Difference</th></tr></thead>'
        f'<tbody>{row_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    st.download_button("Download check-by-check evidence CSV",
                       quality.to_csv(index=False).encode("utf-8"),
                       file_name="campaign_quality_checks.csv", mime="text/csv")
    st.info(
        "**What these results establish:** Summary totals agree across the six comparisons "
        "above, within the stated tolerances. **What they do not establish:** Whether every "
        "individual customer had valid consent at send time, whether each send matches its "
        "approved audience, whether a message was delivered, or whether a holdout experiment "
        "isolated the campaign's effect. These require different, record-level checks."
    )
    st.caption(
        "The separate Campaign Delivery Console displays other checks and flagged-record "
        "counts. They are not included in this dashboard's six-check result because we have "
        "not independently reproduced and verified those results from their underlying queries."
    )
    if st.button("How to read these checks ↗", key="quality_guide", type="tertiary"):
        show_data_guide()

st.divider()
st.caption(
    "Built by Anna Hoang · Synthetic marketing portfolio · Python + SQLite + Streamlit + Plotly · "
    "Campaign-tagged revenue is not a causal measure of incremental revenue."
)
