"""Pievra Campaign API v2 — parse, save, list, edit"""
import os, json
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg, jwt, httpx

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["https://pievra.com"],
    allow_methods=["GET","POST","PUT","OPTIONS"],
    allow_headers=["*"], allow_credentials=True)

DB_URL = os.environ.get("DATABASE_URL","")
JWT_SECRET = os.environ.get("JWT_SECRET","")
JWT_ALGORITHM = "HS256"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")

def get_user(request):
    token = request.cookies.get("pievra_session") or \
            request.headers.get("Authorization","").replace("Bearer ","")
    if not token: return None
    try: return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except: return None

@app.on_event("startup")
async def startup():
    db = await asyncpg.connect(DB_URL)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS pievra_campaigns (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES pievra_users(id),
            brand TEXT, campaign_name TEXT, description TEXT,
            objective TEXT DEFAULT 'Awareness',
            buying_model TEXT DEFAULT 'CPM',
            budget TEXT DEFAULT '50000', kpi TEXT,
            protocols TEXT[], geos TEXT[], environments TEXT[], audiences TEXT[],
            plan_json JSONB, form_data JSONB,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    await db.close()

def build_plan(data):
    budget = float(str(data.get("budget","50000")).replace(",","").replace("$","") or 50000)
    return {
        "brand": data.get("brand",""),
        "campaign_name": data.get("campaign_name",""),
        "objective": data.get("objective","Awareness"),
        "buying_model": data.get("buying_model","CPM"),
        "budget_usd": str(int(budget)),
        "countries": data.get("countries", data.get("country","").split(", ") if data.get("country") else []),
        "environments": data.get("environments",["Web Display"]),
        "recommended_agents": [
            {"name":"PubMatic Premium CTV","protocol":"AdCP","cpm_floor":18.50,"viewability":0.94},
            {"name":"The Trade Desk Open Internet","protocol":"MCP","cpm_floor":12.80,"viewability":0.89},
            {"name":"Index Exchange Display","protocol":"ARTF","cpm_floor":8.20,"viewability":0.82},
        ],
        "projected_kpis": {
            "estimated_impressions": str(int(budget / 14.5 * 1000)),
            "estimated_reach": str(int(budget / 14.5 * 1000 * 0.65)),
            "estimated_cpm": "14.50",
            "estimated_roas": "2.8",
            "viewability_target": "88%",
            "brand_safety": data.get("brand_safety","Standard")
        },
        "protocol_split": {"AdCP":"45%","MCP":"35%","ARTF":"20%"},
        "arbitrage_saving": "18-23% vs single-protocol",
        "flight_recommendation": f"Flight: {data.get('flight_start','TBD')} to {data.get('flight_end','TBD')}",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/campaign")
async def save_campaign(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    plan = build_plan(data)
    db = await asyncpg.connect(DB_URL)
    try:
        status = data.get("status","active")
        cid = await db.fetchval("""
            INSERT INTO pievra_campaigns
            (user_id,brand,campaign_name,description,objective,buying_model,
             budget,kpi,protocols,geos,environments,audiences,plan_json,form_data,status)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING id
        """, int(user["sub"]),
            str(data.get("brand","")), str(data.get("campaign_name","")),
            str(data.get("description","")), str(data.get("objective","Awareness")),
            str(data.get("buying_model","CPM")), str(data.get("budget","50000")),
            str(data.get("kpi","")),
            list(data.get("protocols",["AdCP","MCP","ARTF"])),
            [str(c) for c in data.get("countries", [data.get("country","")] if data.get("country") else [])],
            list(data.get("environments",[])),
            list(data.get("audiences",[])),
            json.dumps(plan), json.dumps(data), status)
        return JSONResponse({"status":"ok","campaign_id":cid,"plan":plan})
    finally:
        await db.close()

@app.get("/api/campaigns")
async def list_campaigns(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        rows = await db.fetch("""
            SELECT id,brand,campaign_name,objective,buying_model,budget,
                   status,created_at,updated_at,plan_json,form_data
            FROM pievra_campaigns WHERE user_id=$1 AND status!='deleted'
            ORDER BY created_at DESC LIMIT 50
        """, int(user["sub"]))
        campaigns = []
        for r in rows:
            d = dict(r)
            d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
            d["updated_at"] = d["updated_at"].isoformat() if d["updated_at"] else None
            d["plan_json"] = json.loads(d["plan_json"]) if d["plan_json"] else {}
            d["form_data"] = json.loads(d["form_data"]) if d["form_data"] else {}
            campaigns.append(d)
        return JSONResponse({"campaigns": campaigns})
    finally:
        await db.close()

@app.put("/api/campaign/{campaign_id}")
async def update_campaign(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    db = await asyncpg.connect(DB_URL)
    try:
        existing = await db.fetchrow(
            "SELECT id FROM pievra_campaigns WHERE id=$1 AND user_id=$2",
            campaign_id, int(user["sub"]))
        if not existing: return JSONResponse({"error":"Not found"},status_code=404)
        plan = build_plan(data)
        status = data.get("status","active")
        await db.execute("""
            UPDATE pievra_campaigns SET
                brand=$1,campaign_name=$2,description=$3,objective=$4,
                buying_model=$5,budget=$6,kpi=$7,protocols=$8,
                environments=$9,plan_json=$10,form_data=$11,status=$12,
                updated_at=NOW()
            WHERE id=$13
        """, str(data.get("brand","")), str(data.get("campaign_name","")),
            str(data.get("description","")), str(data.get("objective","Awareness")),
            str(data.get("buying_model","CPM")), str(data.get("budget","50000")),
            str(data.get("kpi","")),
            list(data.get("protocols",["AdCP","MCP","ARTF"])),
            list(data.get("environments",[])),
            json.dumps(plan), json.dumps(data), status, campaign_id)
        return JSONResponse({"status":"ok","campaign_id":campaign_id,"plan":plan})
    finally:
        await db.close()

@app.delete("/api/campaign/{campaign_id}")
async def delete_campaign(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        await db.execute(
            "UPDATE pievra_campaigns SET status='deleted' WHERE id=$1 AND user_id=$2",
            campaign_id, int(user["sub"]))
        return JSONResponse({"status":"ok"})
    finally:
        await db.close()

@app.post("/api/campaign/parse")
async def parse_campaign(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    msg = data.get("message","")
    if not msg: return JSONResponse({"error":"No message"},status_code=400)

    # Use Claude to parse natural language into campaign fields
    if ANTHROPIC_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version":"2023-06-01", "content-type":"application/json"},
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 800,
                        "system": "You are a programmatic advertising campaign parser. Extract campaign fields from natural language. Return ONLY valid JSON with these fields: brand, campaign_name, description, objective (one of: Awareness/Consideration/Conversion/Retention), buying_model (one of: CPM/CPC/CPA/CPL/CPCV), budget (number as string), kpi, countries (array of country names), environments (array, options: Web Display/Mobile App/CTV Streaming/DOOH/Digital Audio/Social/Native/Online Video), audiences (array of interest categories). If a field is not mentioned, use a sensible default. Return ONLY the JSON object, no markdown.",
                        "messages": [{"role":"user","content": f"Parse this campaign brief into JSON fields:\n\n{msg}"}]
                    }
                )
                result = resp.json()
                raw = result.get("content",[{}])[0].get("text","")
                raw = raw.strip().strip("```json").strip("```").strip()
                parsed = json.loads(raw)
                # Also generate the plan
                plan_data = {**parsed, "protocols": ["AdCP","MCP","ARTF"]}
                plan = build_plan(plan_data)
                db = await asyncpg.connect(DB_URL)
                try:
                    cid = await db.fetchval("""
                        INSERT INTO pievra_campaigns
                        (user_id,brand,campaign_name,description,objective,buying_model,
                         budget,kpi,protocols,geos,environments,audiences,plan_json,form_data,status)
                        VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,'active') RETURNING id
                    """, int(user["sub"]),
                        str(parsed.get("brand","")), str(parsed.get("campaign_name","")),
                        str(parsed.get("description",msg)), str(parsed.get("objective","Awareness")),
                        str(parsed.get("buying_model","CPM")), str(parsed.get("budget","50000")),
                        str(parsed.get("kpi","")),
                        ["AdCP","MCP","ARTF"],
                        parsed.get("countries",[]),
                        parsed.get("environments",[]),
                        parsed.get("audiences",[]),
                        json.dumps(plan), json.dumps(parsed), )
                finally:
                    await db.close()
                return JSONResponse({"status":"ok","parsed":parsed,"plan":plan,"campaign_id":cid})
        except Exception as e:
            print(f"Parse error: {e}")

    # Fallback: save directly without parsing
    plan = build_plan({"description": msg, "campaign_name": "Campaign from chat", "budget":"50000"})
    db = await asyncpg.connect(DB_URL)
    try:
        cid = await db.fetchval("""
            INSERT INTO pievra_campaigns (user_id,brand,campaign_name,description,protocols,plan_json,form_data,status)
            VALUES($1,'','Campaign from chat',$2,$3,$4,$5,'active') RETURNING id
        """, int(user["sub"]), msg, ["AdCP","MCP","ARTF"], json.dumps(plan), json.dumps({"description":msg}))
    finally:
        await db.close()
    return JSONResponse({"status":"ok","plan":plan,"campaign_id":cid})
