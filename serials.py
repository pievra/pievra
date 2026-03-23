"""
Pievra Serial Number Service
IAB OpenRTB 2.6 compatible, GDPR Art.6(1)(b) compliant
No personal data embedded in serial numbers
"""

# Country code mapping for customer SNs
COUNTRY_CODES = {
    "France": "FR", "Germany": "DE", "United Kingdom": "GB",
    "United States": "US", "Spain": "ES", "Italy": "IT",
    "Netherlands": "NL", "Belgium": "BE", "Switzerland": "CH",
    "UAE": "AE", "Saudi Arabia": "SA", "Luxembourg": "LU",
    "Sweden": "SE", "Denmark": "DK", "Norway": "NO",
    "Poland": "PL", "Austria": "AT", "Portugal": "PT",
}

# Campaign type codes (IAB objective mapping)
TYPE_CODES = {
    "Awareness": "AWR",
    "Consideration": "CON",
    "Conversion": "CVR",
    "Retention": "RET",
}

PROTOCOL_STATUS = {
    "AdCP": {"live": False, "label": "Simulation", "color": "yellow",
             "desc": "Protocol Router active. No live AdCP broker connected. Plans use market benchmarks."},
    "MCP":  {"live": True,  "label": "Live — Anthropic API", "color": "green",
             "desc": "Connected to Anthropic Claude API for brief parsing and plan generation."},
    "UCP":  {"live": False, "label": "Simulation", "color": "yellow",
             "desc": "UCP signal objects generated to spec. No live IAB Tech Lab endpoint connected."},
    "ARTF": {"live": True,  "label": "Live — Prebid Server", "color": "green",
             "desc": "Prebid Server running locally. AppNexus, PubMatic, OpenX, Index Exchange adapters active. Web Display, Mobile App, Online Video and Native formats only."},
    "A2A":  {"live": False, "label": "Simulation", "color": "yellow",
             "desc": "A2A agent task objects generated to spec. No live Linux Foundation broker connected."},
}

ARTF_CONSTRAINTS = {
    "environments": ["Web Display", "Mobile App", "Online Video", "Native"],
    "formats": ["300x250", "728x90", "300x600", "160x600", "640x480", "320x50"],
    "bidders": ["AppNexus (Xandr)", "PubMatic", "OpenX", "Index Exchange"],
    "mode": "Test mode — bids are real but not transacted",
    "note": "CTV Streaming, Digital Audio and DOOH require direct DSP API keys (pending)."
}

async def get_or_create_customer_sn(db, user_id: int, country: str = "France") -> str:
    """Get existing or create new customer serial number"""
    existing = await db.fetchrow(
        "SELECT customer_sn FROM pievra_customer_serials WHERE user_id=$1", user_id)
    if existing:
        return existing["customer_sn"]

    from datetime import datetime
    year = str(datetime.now().year)
    cc = COUNTRY_CODES.get(country, "EU")

    # Atomic counter increment
    await db.execute("""
        INSERT INTO pievra_sn_counters (country_code, year, last_seq)
        VALUES ($1, $2, 1)
        ON CONFLICT (country_code, year) DO UPDATE
        SET last_seq = pievra_sn_counters.last_seq + 1
    """, cc, year)

    seq = await db.fetchval(
        "SELECT last_seq FROM pievra_sn_counters WHERE country_code=$1 AND year=$2", cc, year)

    customer_sn = f"PIV-{cc}-{year}-{seq:06d}"

    await db.execute("""
        INSERT INTO pievra_customer_serials (user_id, customer_sn, country_code, year, seq)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id) DO NOTHING
    """, user_id, customer_sn, cc, year, seq)

    return customer_sn

async def get_or_create_campaign_sn(db, campaign_id: int, customer_sn: str) -> str:
    """Generate campaign serial number"""
    existing = await db.fetchrow(
        "SELECT campaign_sn FROM pievra_campaigns WHERE id=$1", campaign_id)
    if existing and existing["campaign_sn"]:
        return existing["campaign_sn"]

    # Count campaigns for this customer
    count = await db.fetchval(
        "SELECT COUNT(*) FROM pievra_campaigns WHERE customer_sn=$1 AND campaign_sn IS NOT NULL",
        customer_sn)
    seq = (count or 0) + 1
    campaign_sn = f"{customer_sn}-CAM-{seq:04d}"

    await db.execute(
        "UPDATE pievra_campaigns SET campaign_sn=$1, customer_sn=$2 WHERE id=$3",
        campaign_sn, customer_sn, campaign_id)

    return campaign_sn

async def get_or_create_flight_sn(db, campaign_id: int, campaign_sn: str,
                                   flight_start: str, objective: str,
                                   impressions_target: int) -> str:
    """Generate IAB-compatible flight serial number"""
    existing = await db.fetchrow(
        "SELECT flight_sn FROM pievra_campaigns WHERE id=$1", campaign_id)
    if existing and existing["flight_sn"]:
        return existing["flight_sn"]

    # Parse flight start date
    try:
        from datetime import datetime
        dt = datetime.strptime(flight_start, "%Y-%m-%d")
        date_str = dt.strftime("%Y%m%d")
    except:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")

    type_code = TYPE_CODES.get(objective, "AWR")
    imp_k = max(1, round(impressions_target / 1000))
    # Cap display at 9999K for flight SN
    imp_display = f"{min(imp_k, 9999)}K"

    flight_sn = f"{campaign_sn}-FLT-{date_str}-{type_code}-{imp_display}"

    await db.execute(
        "UPDATE pievra_campaigns SET flight_sn=$1, campaign_type_code=$2, impressions_target=$3 WHERE id=$4",
        flight_sn, type_code, impressions_target, campaign_id)

    return flight_sn
