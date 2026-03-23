-- Organisation table (future multi-user)
CREATE TABLE IF NOT EXISTS pievra_organisations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    country_code CHAR(2) DEFAULT 'EU',
    plan TEXT DEFAULT 'community',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Link users to organisations
ALTER TABLE pievra_users
    ADD COLUMN IF NOT EXISTS organisation_id INTEGER REFERENCES pievra_organisations(id),
    ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'admin',
    ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'FR';

-- Add advertiser + org to campaigns
ALTER TABLE pievra_campaigns
    ADD COLUMN IF NOT EXISTS advertiser TEXT,
    ADD COLUMN IF NOT EXISTS organisation_id INTEGER,
    ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Populate advertiser from brand where missing
UPDATE pievra_campaigns SET advertiser = brand WHERE advertiser IS NULL AND brand IS NOT NULL;

-- Create default org for existing users
INSERT INTO pievra_organisations (id, name, domain, plan)
VALUES (1, 'Pievra Default', 'pievra.com', 'community')
ON CONFLICT DO NOTHING;

-- Assign all existing users to default org
UPDATE pievra_users SET organisation_id = 1 WHERE organisation_id IS NULL;

-- Assign all campaigns to their user's org
UPDATE pievra_campaigns c
SET organisation_id = u.organisation_id
FROM pievra_users u
WHERE c.user_id = u.id AND c.organisation_id IS NULL;

-- Grant permissions
GRANT ALL ON TABLE pievra_organisations TO pievra_user;
GRANT USAGE, SELECT ON SEQUENCE pievra_organisations_id_seq TO pievra_user;

-- Index for fast filtering
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON pievra_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_advertiser ON pievra_campaigns(advertiser);
CREATE INDEX IF NOT EXISTS idx_campaigns_org ON pievra_campaigns(organisation_id);
