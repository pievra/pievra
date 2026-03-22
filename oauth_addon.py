
# ── GOOGLE OAUTH ──────────────────────────────────────────────────────────────

import urllib.parse as _up

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID","")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET","")
LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID","")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET","")
_STATES = {}

@app.get("/auth/google")
async def google_login(plan: str = "community"):
    state = secrets.token_urlsafe(16)
    _STATES[state] = plan
    params = {"client_id":GOOGLE_CLIENT_ID,"redirect_uri":f"{BASE_URL}/auth/google/callback",
              "response_type":"code","scope":"openid email profile","state":state,"access_type":"offline","prompt":"select_account"}
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + _up.urlencode(params)
    return RedirectResponse(url)

@app.get("/auth/google/callback")
async def google_callback(code: str, state: str, request: Request):
    plan = _STATES.pop(state, "community")
    async with httpx.AsyncClient(timeout=15) as client:
        tr = await client.post("https://oauth2.googleapis.com/token", data={"code":code,"client_id":GOOGLE_CLIENT_ID,"client_secret":GOOGLE_CLIENT_SECRET,"redirect_uri":f"{BASE_URL}/auth/google/callback","grant_type":"authorization_code"})
        tokens = tr.json()
        access_token = tokens.get("access_token","")
        ur = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization":f"Bearer {access_token}"})
        user_info = ur.json()
    email = user_info.get("email","")
    if not email:
        return RedirectResponse(f"{BASE_URL}/signup?error=oauth_failed")
    db = await asyncpg.connect(DB_URL)
    try:
        user = await db.fetchrow("SELECT id,plan,verified FROM pievra_users WHERE email=$1 AND deleted=FALSE", email)
        if user:
            user_id, user_plan = user["id"], user["plan"]
            await db.execute("UPDATE pievra_users SET verified=TRUE,last_login=NOW() WHERE id=$1", user_id)
        else:
            user_id = await db.fetchval("INSERT INTO pievra_users (email,plan,verified,gdpr_consent,gdpr_consent_at) VALUES ($1,$2,TRUE,TRUE,NOW()) RETURNING id", email, plan)
            user_plan = plan
        jwt_token = make_jwt(user_id, email, user_plan)
        await db.execute("INSERT INTO pievra_sessions (user_id,token,expires_at) VALUES ($1,$2,NOW()+INTERVAL '30 days')", user_id, jwt_token)
        resp = RedirectResponse(f"{BASE_URL}/dashboard?welcome=1")
        resp.set_cookie("pievra_session", jwt_token, max_age=30*86400, secure=True, httponly=True, samesite="lax", domain="pievra.com")
        # Also set non-httponly for JS localStorage fallback
        resp.set_cookie("pievra_token_pub", jwt_token, max_age=30*86400, secure=True, httponly=False, samesite="lax", domain="pievra.com")
        return resp
    finally:
        await db.close()

@app.get("/auth/linkedin")
async def linkedin_login(plan: str = "community"):
    state = secrets.token_urlsafe(16)
    _STATES[state] = plan
    params = {"response_type":"code","client_id":LINKEDIN_CLIENT_ID,"redirect_uri":f"{BASE_URL}/auth/linkedin/callback","state":state,"scope":"openid profile email"}
    url = "https://www.linkedin.com/oauth/v2/authorization?" + _up.urlencode(params)
    return RedirectResponse(url)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(code: str, state: str, request: Request):
    plan = _STATES.pop(state, "community")
    async with httpx.AsyncClient(timeout=15) as client:
        tr = await client.post("https://www.linkedin.com/oauth/v2/accessToken",
            data={"grant_type":"authorization_code","code":code,"redirect_uri":f"{BASE_URL}/auth/linkedin/callback","client_id":LINKEDIN_CLIENT_ID,"client_secret":LINKEDIN_CLIENT_SECRET},
            headers={"Content-Type":"application/x-www-form-urlencoded"})
        tokens = tr.json()
        access_token = tokens.get("access_token","")
        ur = await client.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization":f"Bearer {access_token}"})
        user_info = ur.json()
    email = user_info.get("email","")
    if not email:
        return RedirectResponse(f"{BASE_URL}/signup?error=oauth_failed")
    db = await asyncpg.connect(DB_URL)
    try:
        user = await db.fetchrow("SELECT id,plan,verified FROM pievra_users WHERE email=$1 AND deleted=FALSE", email)
        if user:
            user_id, user_plan = user["id"], user["plan"]
            await db.execute("UPDATE pievra_users SET verified=TRUE,last_login=NOW() WHERE id=$1", user_id)
        else:
            user_id = await db.fetchval("INSERT INTO pievra_users (email,plan,verified,gdpr_consent,gdpr_consent_at) VALUES ($1,$2,TRUE,TRUE,NOW()) RETURNING id", email, plan)
            user_plan = plan
        jwt_token = make_jwt(user_id, email, user_plan)
        await db.execute("INSERT INTO pievra_sessions (user_id,token,expires_at) VALUES ($1,$2,NOW()+INTERVAL '30 days')", user_id, jwt_token)
        resp = RedirectResponse(f"{BASE_URL}/dashboard?welcome=1")
        resp.set_cookie("pievra_session", jwt_token, max_age=30*86400, secure=True, httponly=True, samesite="lax", domain="pievra.com")
        resp.set_cookie("pievra_token_pub", jwt_token, max_age=30*86400, secure=True, httponly=False, samesite="lax", domain="pievra.com")
        return resp
    finally:
        await db.close()
