-- ===========================================================================
-- CAMPAIGN ANALYTICS SCHEMA
-- SQLite. Star-schema style: customers/campaigns are dimensions;
-- audience_selection/sends/events/orders are facts.
-- ===========================================================================

CREATE TABLE customers (
    customer_id         INTEGER PRIMARY KEY,
    signup_date          TEXT NOT NULL,        -- YYYY-MM-DD
    acquisition_channel   TEXT NOT NULL,        -- Paid Social, Organic Search, Referral, Events, Paid Search
    region                TEXT NOT NULL,
    birth_year            INTEGER,
    consent_email         INTEGER NOT NULL,     -- 1/0
    consent_sms           INTEGER NOT NULL,     -- 1/0
    opted_out_date        TEXT                  -- NULL if never opted out
);

CREATE TABLE campaigns (
    campaign_id    INTEGER PRIMARY KEY,
    campaign_name  TEXT NOT NULL,
    channel        TEXT NOT NULL,               -- Email, SMS, Paid Social, Display
    objective      TEXT NOT NULL,               -- Acquisition, Retention, Winback, Cross-sell
    start_date     TEXT NOT NULL,
    end_date       TEXT NOT NULL,
    cost           REAL NOT NULL
);

-- Every candidate customer considered for a campaign, and what happened to
-- them BEFORE send: sent, suppressed (with reason), or held out as a
-- control/test group for incrementality measurement. This table is the
-- audit trail an ordinary "results dashboard" project never has.
CREATE TABLE audience_selection (
    selection_id        INTEGER PRIMARY KEY,
    campaign_id          INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    customer_id          INTEGER NOT NULL REFERENCES customers(customer_id),
    status               TEXT NOT NULL,          -- 'sent' | 'suppressed' | 'control_holdout'
    suppression_reason   TEXT                    -- no_consent | opted_out | frequency_cap |
                                                   -- recent_purchase_exclusion | not_yet_signed_up
);

CREATE TABLE sends (
    send_id       INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    send_date     TEXT NOT NULL,
    channel       TEXT NOT NULL
);

CREATE TABLE events (
    event_id     INTEGER PRIMARY KEY,
    send_id      INTEGER NOT NULL REFERENCES sends(send_id),
    event_type   TEXT NOT NULL,      -- 'open' | 'click'
    event_date   TEXT NOT NULL
);

-- Orders are NOT pre-labelled with a campaign for organic purchases
-- (campaign_id is NULL) so that attribution has to be worked out in SQL --
-- exactly the ambiguity a real analyst faces.
CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date    TEXT NOT NULL,
    revenue       REAL NOT NULL,
    campaign_id   INTEGER REFERENCES campaigns(campaign_id)  -- only set for campaign-induced orders in the generator; treat as unknown/derive via attribution in real analysis
);

CREATE INDEX idx_sends_customer ON sends(customer_id);
CREATE INDEX idx_sends_campaign ON sends(campaign_id);
CREATE INDEX idx_events_send ON events(send_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_audience_campaign ON audience_selection(campaign_id);
CREATE INDEX idx_audience_customer ON audience_selection(customer_id);
