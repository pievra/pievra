
# ── PROTOCOL STATUS ────────────────────────────────────────────────────────────

@app.get("/api/protocol/status")
async def protocol_status():
    """Live vs simulation status for all 5 protocols"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("serials", "/opt/pievra-newsletter/serials.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Check Prebid Server liveness
    prebid_live = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as c:
            r = await c.get("http://127.0.0.1:8080/status")
            prebid_live = r.status_code in [200, 204]
    except:
        pass

    status = dict(mod.PROTOCOL_STATUS)
    status["ARTF"]["live"] = prebid_live
    status["ARTF"]["label"] = "Live — Prebid Server" if prebid_live else "Prebid Server starting..."

    return JSONResponse({
        "protocols": status,
        "artf_constraints": mod.ARTF_CONSTRAINTS,
        "last_checked": datetime.now(timezone.utc).isoformat()
    })

# ── SERIAL NUMBERS ─────────────────────────────────────────────────────────────

@app.get("/api/customer/sn")
async def get_customer_sn(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"}, status_code=401)
    import importlib.util
    spec = importlib.util.spec_from_file_location("serials", "/opt/pievra-newsletter/serials.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    db = await asyncpg.connect(DB_URL)
    try:
        sn = await mod.get_or_create_customer_sn(db, int(user["sub"]))
        return JSONResponse({"customer_sn": sn})
    finally:
        await db.close()

@app.post("/api/campaign/{campaign_id}/serials")
async def assign_serials(campaign_id: int, request: Request):
    """Assign all serial numbers to a campaign"""
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"}, status_code=401)
    data = await request.json()
    import importlib.util
    spec = importlib.util.spec_from_file_location("serials", "/opt/pievra-newsletter/serials.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    db = await asyncpg.connect(DB_URL)
    try:
        row = await db.fetchrow(
            "SELECT id,plan_json,objective,budget FROM pievra_campaigns WHERE id=$1 AND user_id=$2",
            campaign_id, int(user["sub"]))
        if not row: return JSONResponse({"error":"Not found"}, status_code=404)
        plan = json.loads(row["plan_json"]) if row["plan_json"] else {}
        kpis = plan.get("projected_kpis", {})
        imp = int(kpis.get("estimated_impressions", 0) or 0)
        country = data.get("country", "France")
        objective = row["objective"] or "Awareness"
        flight_start = data.get("flight_start", plan.get("flight_start", ""))

        customer_sn = await mod.get_or_create_customer_sn(db, int(user["sub"]), country)
        campaign_sn = await mod.get_or_create_campaign_sn(db, campaign_id, customer_sn)
        flight_sn   = await mod.get_or_create_flight_sn(
            db, campaign_id, campaign_sn, flight_start, objective, imp)

        return JSONResponse({
            "customer_sn": customer_sn,
            "campaign_sn": campaign_sn,
            "flight_sn": flight_sn,
            "iab_deal_id": flight_sn,
            "gdpr_basis": "Art.6(1)(b) GDPR - performance of contract"
        })
    finally:
        await db.close()

# ── GO-LIVE CONSENT ────────────────────────────────────────────────────────────

@app.post("/api/campaign/{campaign_id}/consent")
async def record_consent(campaign_id: int, request: Request):
    """Record explicit go-live consent with timestamp and IP"""
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"}, status_code=401)
    data = await request.json()

    required = ["billing_accepted","intermediary_accepted","gdpr_accepted","signature"]
    for field in required:
        if not data.get(field):
            return JSONResponse({"error": f"Missing required consent: {field}"}, status_code=400)

    client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For","unknown")
    consent_at = datetime.now(timezone.utc)

    db = await asyncpg.connect(DB_URL)
    try:
        row = await db.fetchrow(
            "SELECT id,campaign_sn,flight_sn,customer_sn FROM pievra_campaigns WHERE id=$1 AND user_id=$2",
            campaign_id, int(user["sub"]))
        if not row: return JSONResponse({"error":"Not found"}, status_code=404)

        await db.execute("""
            UPDATE pievra_campaigns SET
                go_live_consent = TRUE,
                go_live_consent_at = $1,
                go_live_consent_ip = $2,
                billing_accepted = TRUE,
                status = 'active'
            WHERE id = $3
        """, consent_at, client_ip, campaign_id)

        return JSONResponse({
            "status": "consent_recorded",
            "campaign_id": campaign_id,
            "campaign_sn": row["campaign_sn"],
            "flight_sn": row["flight_sn"],
            "consented_at": consent_at.isoformat(),
            "consented_ip": client_ip,
            "gdpr_basis": "Art.6(1)(b) GDPR - performance of contract",
            "billing_terms": "Full campaign budget charged on delivery. Pievra acts as intermediary only. No performance guarantees.",
            "record_kept_until": "7 years from campaign end date per EU accounting law"
        })
    finally:
        await db.close()

@app.get("/api/campaign/{campaign_id}/consent")
async def get_consent_status(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"}, status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        row = await db.fetchrow("""
            SELECT go_live_consent, go_live_consent_at, billing_accepted,
                   campaign_sn, flight_sn, customer_sn, status
            FROM pievra_campaigns WHERE id=$1 AND user_id=$2
        """, campaign_id, int(user["sub"]))
        if not row: return JSONResponse({"error":"Not found"}, status_code=404)
        d = dict(row)
        if d["go_live_consent_at"]:
            d["go_live_consent_at"] = d["go_live_consent_at"].isoformat()
        return JSONResponse(d)
    finally:
        await db.close()
