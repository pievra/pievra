-- Customer serial numbers
CREATE TABLE IF NOT EXISTS pievra_customer_serials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES pievra_users(id),
    customer_sn TEXT NOT NULL UNIQUE,
    country_code CHAR(2) NOT NULL,
    year CHAR(4) NOT NULL,
    seq INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign serial numbers (links to pievra_campaigns)
ALTER TABLE pievra_campaigns
    ADD COLUMN IF NOT EXISTS campaign_sn TEXT,
    ADD COLUMN IF NOT EXISTS flight_sn TEXT,
    ADD COLUMN IF NOT EXISTS customer_sn TEXT,
    ADD COLUMN IF NOT EXISTS go_live_consent BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS go_live_consent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS go_live_consent_ip TEXT,
    ADD COLUMN IF NOT EXISTS billing_accepted BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS impressions_target INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS campaign_type_code TEXT DEFAULT 'AWR',
    ADD COLUMN IF NOT EXISTS flight_start TEXT,
    ADD COLUMN IF NOT EXISTS flight_end TEXT;

-- Sequence counter per country per year
CREATE TABLE IF NOT EXISTS pievra_sn_counters (
    country_code CHAR(2) NOT NULL,
    year CHAR(4) NOT NULL,
    last_seq INTEGER DEFAULT 0,
    PRIMARY KEY (country_code, year)
);

-- Index for IAB bid stream lookup
CREATE INDEX IF NOT EXISTS idx_campaigns_flight_sn ON pievra_campaigns(flight_sn);
CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_sn ON pievra_campaigns(campaign_sn);
CREATE INDEX IF NOT EXISTS idx_campaigns_customer_sn ON pievra_campaigns(customer_sn);
