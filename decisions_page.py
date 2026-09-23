
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


EXPORT_DIR = Path(__file__).resolve().parent / "powerbi_exports"

NAVY = "#142C3A"
TEAL = "#0E807A"
GOLD = "#B47D25"
RED = "#A94A38"
MUTED = "#65778A"


@st.cache_data
def load_decision_data():
    """Read the existing SQL-derived exports."""
    queue = pd.read_csv(EXPORT_DIR / "campaign_decision_queue.csv")
    promising = pd.read_csv(EXPORT_DIR / "promising_campaigns.csv")
    opportunities = pd.read_csv(
        EXPORT_DIR / "customer_opportunity_review.csv"
    )

    return queue, promising, opportunities


def find_column(df, *candidates):
    """Return the first available column name."""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def money(value):
    return f"${value:,.0f}"


def number(value):
    return pd.to_numeric(value, errors="coerce")


def render_decisions():
    st.markdown(
        """
        <style>
        .decision-eyebrow {
            color: #08766F;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .decision-heading {
            color: #142C3A;
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 0.4rem;
        }

        .decision-subtitle {
            color: #65778A;
            margin-bottom: 1.5rem;
        }

        .decision-section {
            color: #142C3A;
            font-size: 1.35rem;
            font-weight: 750;
            margin-top: 1.4rem;
            margin-bottom: 0.5rem;
        }

        .decision-note {
            background: #EAF8F5;
            border: 1px solid #B6E0D8;
            border-radius: 9px;
            padding: 15px 18px;
            color: #173B42;
            margin: 14px 0 22px;
            line-height: 1.55;
        }

        .decision-small {
            color: #65778A;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    queue, promising, opportunities = load_decision_data()

    # -------------------------------------------------------
    # PAGE HEADER
    # -------------------------------------------------------

    st.markdown(
        '<div class="decision-eyebrow">Management decisions</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="decision-heading">Which campaigns need '
        'a decision first?</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="decision-subtitle">'
        'Review recorded spend, commercial performance and '
        'exploratory conversion evidence before deciding what '
        'to maintain, investigate or re-test.'
        '</div>',
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------
    # 1. DECISION SUMMARY
    # -------------------------------------------------------

    st.markdown(
        '<div class="decision-section">Decision queue at a glance</div>',
        unsafe_allow_html=True,
    )

    action_col = "recommended_action"
    spend_col = "spend"

    queue[spend_col] = number(queue[spend_col]).fillna(0)

    action_summary = (
        queue.groupby(action_col, dropna=False)
        .agg(
            campaigns=("campaign_id", "nunique"),
            spend=(spend_col, "sum"),
        )
        .reset_index()
        .sort_values("campaigns", ascending=False)
    )

    # These are the action labels produced by your SQL export.
    preferred_actions = [
        "Review spend and diagnose",
        "Limit spend and re-test",
        "Re-test and improve measurement",
        "Maintain and optimise",
    ]

    ordered_actions = [
        action for action in preferred_actions
        if action in action_summary[action_col].values
    ]

    ordered_actions += [
        action for action in action_summary[action_col].tolist()
        if action not in ordered_actions
    ]

    summary_cols = st.columns(len(ordered_actions) + 1)

    for i, action in enumerate(ordered_actions):
        row = action_summary.loc[
            action_summary[action_col] == action
        ].iloc[0]

        with summary_cols[i]:
            with st.container(border=True):
                st.caption(action.upper())
                st.metric("Campaigns", int(row["campaigns"]))
                st.caption(f"{money(row['spend'])} recorded spend")

    with summary_cols[-1]:
        with st.container(border=True):
            st.caption("TOTAL CAMPAIGNS")
            st.metric("In decision queue", queue["campaign_id"].nunique())
            st.caption("Historical synthetic portfolio")

    st.markdown(
        '<div class="decision-note">'
        '<strong>How to use this page:</strong> These categories are '
        'SQL-generated review recommendations, not automatic approval '
        'to increase or stop spending. Check eligibility, campaign '
        'objectives, measurement quality and commercial context '
        'before taking action.'
        '</div>',
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------
    # 2. PROMISING CAMPAIGNS
    # -------------------------------------------------------

    st.markdown(
        '<div class="decision-section">'
        'Which campaigns show promising signals worth re-testing?'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="decision-small">'
        'These campaigns were identified by the existing SQL analysis. '
        'Positive exploratory lift is a reason to investigate further, '
        'not proof of incremental revenue.'
        '</div>',
        unsafe_allow_html=True,
    )

    if promising.empty:
        st.info("No campaigns are currently in the promising-campaign export.")

    else:
        promising["roas"] = number(promising["roas"])

        promising = promising.sort_values(
            "roas", ascending=False, na_position="last"
        )

        top = promising.head(10)

        for start in range(0, len(top), 2):
            columns = st.columns(2)

            for j, (_, campaign) in enumerate(
                top.iloc[start:start + 2].iterrows()
            ):
                with columns[j]:
                    with st.container(border=True):
                        st.markdown(
                            f"**{campaign['campaign_name']}**"
                        )

                        roas = campaign["roas"]

                        if pd.notna(roas):
                            st.markdown(
                                f"### {roas:.1f}× tagged ROAS"
                            )

                        lift = number(
                            campaign.get("estimated_lift_pp")
                        )

                        lower = number(
                            campaign.get("lift_ci_lower_pp")
                        )

                        upper = number(
                            campaign.get("lift_ci_upper_pp")
                        )

                        if (
                            pd.notna(lift)
                            and pd.notna(lower)
                            and pd.notna(upper)
                        ):
                            st.caption(
                                f"Observed lift: {lift:+.1f} percentage "
                                f"points · 95% interval "
                                f"[{lower:+.1f}, {upper:+.1f}]"
                            )

                        next_step = campaign.get(
                            "proposed_next_step"
                        )

                        if pd.notna(next_step):
                            st.caption(f"Next step: {next_step}")

    with st.expander("View all promising campaigns"):
        st.dataframe(
            promising,
            width="stretch",
            hide_index=True,
        )

    # -------------------------------------------------------
    # 3. FULL DECISION QUEUE
    # -------------------------------------------------------

    st.markdown(
        '<div class="decision-section">'
        'Which campaigns require a management decision first?'
        '</div>',
        unsafe_allow_html=True,
    )

    filter1, filter2, filter3, filter4 = st.columns(
        [1.4, 1, 1, 1.2]
    )

    with filter1:
        search = st.text_input(
            "Search campaign",
            placeholder="Campaign name...",
            key="decision_search",
        )

    with filter2:
        selected_action = st.selectbox(
            "Recommended action",
            ["All actions"] + sorted(
                queue["recommended_action"].dropna().unique().tolist()
            ),
            key="decision_action",
        )

    with filter3:
        selected_channel = st.selectbox(
            "Channel",
            ["All channels"] + sorted(
                queue["channel"].dropna().unique().tolist()
            ),
            key="decision_channel",
        )

    with filter4:
        selected_status = st.selectbox(
            "Commercial status",
            ["All statuses"] + sorted(
                queue["commercial_status"].dropna().unique().tolist()
            ),
            key="decision_commercial",
        )

    filtered = queue.copy()

    if search:
        filtered = filtered[
            filtered["campaign_name"].astype(str).str.contains(
                search, case=False, na=False, regex=False
            )
        ]

    if selected_action != "All actions":
        filtered = filtered[
            filtered["recommended_action"] == selected_action
        ]

    if selected_channel != "All channels":
        filtered = filtered[
            filtered["channel"] == selected_channel
        ]

    if selected_status != "All statuses":
        filtered = filtered[
            filtered["commercial_status"] == selected_status
        ]

    filtered = filtered.sort_values("spend", ascending=False)

    st.caption(
        f"{len(filtered)} of {len(queue)} campaign records shown. "
        "Sorted by recorded spend; click a column heading to sort."
    )

    display_columns = [
        "campaign_name",
        "channel",
        "objective",
        "spend",
        "roas",
        "commercial_status",
        "evidence_status",
        "recommended_action",
    ]

    available_columns = [
        c for c in display_columns if c in filtered.columns
    ]

    st.dataframe(
        filtered[available_columns],
        width="stretch",
        height=460,
        hide_index=True,
        column_config={
            "campaign_name": st.column_config.TextColumn(
                "Campaign", width="large"
            ),
            "channel": "Channel",
            "objective": "Objective",
            "spend": st.column_config.NumberColumn(
                "Spend", format="$%.2f"
            ),
            "roas": st.column_config.NumberColumn(
                "Tagged ROAS", format="%.2f×"
            ),
            "commercial_status": "Commercial status",
            "evidence_status": "Evidence",
            "recommended_action": st.column_config.TextColumn(
                "Recommended action", width="large"
            ),
        },
    )

    st.download_button(
        "Download filtered decision queue",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_campaign_decision_queue.csv",
        mime="text/csv",
        key="download_decision_queue",
    )

    # -------------------------------------------------------
    # 4. CUSTOMER OPPORTUNITIES
    # -------------------------------------------------------

    st.markdown(
        '<div class="decision-section">'
        'Which valuable customers warrant an eligibility review?'
        '</div>',
        unsafe_allow_html=True,
    )

    customer_col = find_column(
        opportunities, "customer_id"
    )

    value_col = find_column(
        opportunities, "monetary", "lifetime_value"
    )

    acquisition_col = find_column(
        opportunities, "acquisition_channel"
    )

    opportunity_cols = st.columns(3)

    with opportunity_cols[0]:
        with st.container(border=True):
            st.metric(
                "Customers under review",
                opportunities[customer_col].nunique()
                if customer_col else len(opportunities),
            )

    with opportunity_cols[1]:
        with st.container(border=True):
            total_value = (
                number(opportunities[value_col]).fillna(0).sum()
                if value_col else 0
            )
            st.metric(
                "Recorded historical value",
                money(total_value),
            )

    with opportunity_cols[2]:
        with st.container(border=True):
            if acquisition_col and not opportunities.empty:
                largest_source = (
                    opportunities[acquisition_col]
                    .fillna("Unknown")
                    .value_counts()
                    .idxmax()
                )
            else:
                largest_source = "Not available"

            st.metric(
                "Largest acquisition source",
                largest_source,
            )

    st.markdown(
        '<div class="decision-note">'
        '<strong>Recommended next step:</strong> Review why these '
        'customers are outside the current send audiences. Recheck '
        'current consent, product eligibility, suppression reasons '
        'and contact-frequency rules before considering them for '
        'a new campaign. Historical value is not guaranteed '
        'future revenue.'
        '</div>',
        unsafe_allow_html=True,
    )

  
    with st.expander("Review customer opportunity records"):
        st.dataframe(
            opportunities,
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "All findings are based on synthetic historical data. "
        "Campaign-tagged ROAS and observed conversion differences "
        "do not establish causal incremental revenue."
    )