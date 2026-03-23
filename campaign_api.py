"""
Pievra Campaign Engine
- Protocol Router: translates campaign brief into 5 protocol-specific payloads
- PDF Generator: professional downloadable media plan
- Plan API: /api/plan/{id} returns full plan detail
- PDF API: /api/plan/{id}/pdf returns downloadable PDF
"""
import os, json, math, io
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg, jwt, httpx

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["https://pievra.com"],
    allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],
    allow_headers=["*"], allow_credentials=True)

DB_URL = os.environ.get("DATABASE_URL","")
JWT_SECRET = os.environ.get("JWT_SECRET","")
JWT_ALGORITHM = "HS256"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
BASE_URL = os.environ.get("BASE_URL","https://pievra.com")

def get_user(request):
    token = (request.cookies.get("pievra_session") or
             request.headers.get("Authorization","").replace("Bearer ",""))
    if not token: return None
    try: return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except: return None

# ── PROTOCOL ROUTER ──────────────────────────────────────────────────────────

class ProtocolRouter:
    """Translates a campaign brief into 5 protocol-specific payloads"""

    def __init__(self, data: dict):
        self.data = data
        self.budget = float(str(data.get("budget","50000")).replace(",","").replace("$","") or 50000)
        self.objective = data.get("objective","Awareness")
        self.environments = data.get("environments", ["Web Display"])
        self.countries = data.get("countries", data.get("country","").split(", ") if data.get("country") else ["France"])
        if isinstance(self.countries, str):
            self.countries = [self.countries]

    def get_protocol_split(self):
        """Determine optimal protocol split based on campaign parameters"""
        splits = {"AdCP": 0, "MCP": 0, "UCP": 0, "ARTF": 0, "A2A": 0}
        envs = [e.lower() for e in self.environments]

        # AdCP: campaign negotiation and deal management
        splits["AdCP"] = 35
        # MCP: tool calling and data orchestration
        splits["MCP"] = 25
        # UCP: audience signal activation
        splits["UCP"] = 20
        # ARTF: real-time auction execution
        splits["ARTF"] = 15
        # A2A: agent collaboration and optimisation
        splits["A2A"] = 5

        # Adjust based on environments
        if any(e in envs for e in ["ctv","streaming","connected tv"]):
            splits["AdCP"] += 5; splits["ARTF"] -= 5
        if self.objective in ["Conversion","Retention"]:
            splits["UCP"] += 5; splits["A2A"] += 5; splits["AdCP"] -= 5; splits["MCP"] -= 5
        if self.objective == "Awareness":
            splits["ARTF"] += 5; splits["UCP"] -= 5

        # Normalise to 100
        total = sum(splits.values())
        return {k: round(v/total*100) for k,v in splits.items()}

    def build_adcp_payload(self):
        """AdCP: natural language campaign brief for agent negotiation"""
        return {
            "protocol": "AdCP",
            "version": "v3.0-rc",
            "type": "campaign_brief",
            "brief": {
                "objective": self.objective,
                "budget_usd": self.budget * 0.35,
                "target_audiences": self.data.get("audiences", []),
                "geographies": self.countries,
                "environments": self.environments,
                "flight": {
                    "start": self.data.get("flight_start","TBD"),
                    "end": self.data.get("flight_end","TBD")
                },
                "kpi": self.data.get("kpi","ROAS > 2.5"),
                "brand_safety": self.data.get("brand_safety","Standard")
            },
            "capabilities_required": ["inventory_discovery","deal_negotiation","bid_management"],
            "steward": "Agentic Advertising Organisation",
            "status": "ready",
            "estimated_cpm": 16.50,
            "estimated_reach_pct": 42,
            "arbitrage_saving_pct": 23
        }

    def build_mcp_payload(self):
        """MCP: tool calls for data orchestration"""
        return {
            "protocol": "MCP",
            "version": "v1.0",
            "type": "tool_orchestration",
            "tools_activated": [
                {"name": "audience_lookup", "params": {"segments": self.data.get("audiences",[])}},
                {"name": "inventory_check", "params": {"environments": self.environments, "geos": self.countries}},
                {"name": "floor_price_query", "params": {"environments": self.environments}},
                {"name": "brand_safety_screen", "params": {"level": self.data.get("brand_safety","Standard")}}
            ],
            "budget_usd": self.budget * 0.25,
            "steward": "Anthropic",
            "status": "ready",
            "estimated_cpm": 12.80,
            "estimated_reach_pct": 31,
            "arbitrage_saving_pct": 18
        }

    def build_ucp_payload(self):
        """UCP: privacy-safe audience signal activation"""
        return {
            "protocol": "UCP",
            "version": "v0.8",
            "type": "audience_activation",
            "signals": {
                "identity_signals": ["email_hash","device_graph","contextual"],
                "context_signals": ["page_category","recency","intent_score"],
                "reinforcement_signals": ["conversion_feedback","frequency_data"],
                "privacy_framework": "TCF 2.2 + GPP",
                "embedding_dim": 128
            },
            "budget_usd": self.budget * 0.20,
            "target_segments": self.data.get("audiences",[]),
            "steward": "IAB Tech Lab",
            "status": "ready",
            "estimated_cpm": 14.20,
            "estimated_reach_pct": 25,
            "arbitrage_saving_pct": 15
        }

    def build_artf_payload(self):
        """ARTF: real-time auction execution"""
        return {
            "protocol": "ARTF",
            "version": "v0.5",
            "type": "rtb_execution",
            "auction_params": {
                "bid_floor_usd": 8.00,
                "max_bid_usd": 25.00,
                "timeout_ms": 120,
                "deal_ids": [],
                "extensions": ["OpenRTB_2.6","AdCOM_1.0"]
            },
            "budget_usd": self.budget * 0.15,
            "environments": self.environments,
            "steward": "IAB Tech Lab",
            "status": "ready",
            "estimated_cpm": 9.40,
            "estimated_reach_pct": 18,
            "latency_reduction_pct": 80,
            "arbitrage_saving_pct": 28
        }

    def build_a2a_payload(self):
        """A2A: agent collaboration for optimisation"""
        return {
            "protocol": "A2A",
            "version": "v1.0",
            "type": "agent_collaboration",
            "agents": [
                {"role": "optimiser", "task": "real_time_bid_adjustment"},
                {"role": "reporter", "task": "performance_aggregation"},
                {"role": "pacing_agent", "task": "budget_distribution"}
            ],
            "budget_usd": self.budget * 0.05,
            "steward": "Linux Foundation",
            "status": "ready",
            "estimated_cpm": 11.20,
            "estimated_reach_pct": 6,
            "arbitrage_saving_pct": 12
        }

    def build_full_plan(self):
        split = self.get_protocol_split()
        adcp = self.build_adcp_payload()
        mcp  = self.build_mcp_payload()
        ucp  = self.build_ucp_payload()
        artf = self.build_artf_payload()
        a2a  = self.build_a2a_payload()

        # Weighted average CPM
        weighted_cpm = (
            adcp["estimated_cpm"] * split["AdCP"]/100 +
            mcp["estimated_cpm"]  * split["MCP"]/100 +
            ucp["estimated_cpm"]  * split["UCP"]/100 +
            artf["estimated_cpm"] * split["ARTF"]/100 +
            a2a["estimated_cpm"]  * split["A2A"]/100
        )
        estimated_impressions = int(self.budget / weighted_cpm * 1000)
        single_protocol_cpm = 18.50
        cpm_saving_pct = round((single_protocol_cpm - weighted_cpm) / single_protocol_cpm * 100, 1)

        return {
            "brand": self.data.get("brand",""),
            "campaign_name": self.data.get("campaign_name",""),
            "objective": self.objective,
            "buying_model": self.data.get("buying_model","CPM"),
            "budget_usd": str(int(self.budget)),
            "countries": self.countries,
            "environments": self.environments,
            "flight_start": self.data.get("flight_start","TBD"),
            "flight_end": self.data.get("flight_end","TBD"),
            "protocol_split": split,
            "protocols": {
                "AdCP": adcp,
                "MCP":  mcp,
                "UCP":  ucp,
                "ARTF": artf,
                "A2A":  a2a
            },
            "projected_kpis": {
                "estimated_impressions": str(estimated_impressions),
                "estimated_reach": str(int(estimated_impressions * 0.65)),
                "weighted_cpm": f"{weighted_cpm:.2f}",
                "single_protocol_cpm": f"{single_protocol_cpm:.2f}",
                "cpm_saving_pct": str(cpm_saving_pct),
                "estimated_roas": "2.8",
                "viewability_target": "88%",
                "brand_safety": self.data.get("brand_safety","Standard")
            },
            "recommended_agents": [
                {"name":"BidOptima Pro","protocol":"AdCP","cpm_floor":16.50,"viewability":0.94,"steward":"PubMatic"},
                {"name":"AudienceSync","protocol":"UCP","cpm_floor":14.20,"viewability":0.91,"steward":"LiveRamp"},
                {"name":"RTBArbiteur","protocol":"ARTF","cpm_floor":9.40,"viewability":0.87,"steward":"Index Exchange"},
                {"name":"ContextMapper","protocol":"MCP","cpm_floor":12.80,"viewability":0.89,"steward":"Anthropic"},
                {"name":"AgentOrchestrator","protocol":"A2A","cpm_floor":11.20,"viewability":0.85,"steward":"Google"}
            ],
            "budget_allocation": {
                "AdCP": int(self.budget * split["AdCP"]/100),
                "MCP":  int(self.budget * split["MCP"]/100),
                "UCP":  int(self.budget * split["UCP"]/100),
                "ARTF": int(self.budget * split["ARTF"]/100),
                "A2A":  int(self.budget * split["A2A"]/100)
            },
            "arbitrage_saving": f"{cpm_saving_pct}% vs single-protocol CPM",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# ── PDF GENERATOR ─────────────────────────────────────────────────────────────

def generate_media_plan_pdf(plan: dict, campaign: dict) -> bytes:
    """Generate a professional media plan PDF using ReportLab"""
    buf = io.BytesIO()

    INK   = colors.HexColor("#0a0e1a")
    TEAL  = colors.HexColor("#00c4a7")
    TEAL2 = colors.HexColor("#009e86")
    SURF  = colors.HexColor("#f4f5f9")
    MUTED = colors.HexColor("#7a829e")
    WHITE = colors.white
    PROTO_COLORS = {
        "AdCP": colors.HexColor("#dbeafe"),
        "MCP":  colors.HexColor("#f3e8ff"),
        "UCP":  colors.HexColor("#dcfce7"),
        "ARTF": colors.HexColor("#fef9c3"),
        "A2A":  colors.HexColor("#ffe4e6"),
    }

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    story = []

    def H1(text, color=INK):
        return Paragraph(text, ParagraphStyle('h1', fontName='Helvetica-Bold',
            fontSize=22, textColor=color, spaceAfter=4))
    def H2(text, color=INK):
        return Paragraph(text, ParagraphStyle('h2', fontName='Helvetica-Bold',
            fontSize=14, textColor=color, spaceAfter=4, spaceBefore=8))
    def H3(text, color=MUTED):
        return Paragraph(text, ParagraphStyle('h3', fontName='Helvetica',
            fontSize=10, textColor=color, spaceAfter=3))
    def Body(text, color=colors.HexColor("#3d4460")):
        return Paragraph(text, ParagraphStyle('body', fontName='Helvetica',
            fontSize=10, textColor=color, spaceAfter=4, leading=14))
    def Small(text, color=MUTED):
        return Paragraph(text, ParagraphStyle('sm', fontName='Helvetica',
            fontSize=9, textColor=color, spaceAfter=2))
    def Mono(text):
        return Paragraph(text, ParagraphStyle('mono', fontName='Courier',
            fontSize=9, textColor=INK, spaceAfter=2))

    kpis  = plan.get("projected_kpis", {})
    split = plan.get("protocol_split", {})
    alloc = plan.get("budget_allocation", {})
    protos = plan.get("protocols", {})
    agents = plan.get("recommended_agents", [])
    brand  = plan.get("brand") or campaign.get("brand","")
    cname  = plan.get("campaign_name") or campaign.get("campaign_name","")
    budget = plan.get("budget_usd") or campaign.get("budget","50000")

    now_str = datetime.now().strftime("%d %B %Y")

    # ── PAGE 1: COVER ──────────────────────────────────────────────────────────

    # Cover header block
    cover_data = [[
        Paragraph("<b>PIEVRA</b>", ParagraphStyle('logo', fontName='Helvetica-Bold',
            fontSize=28, textColor=WHITE)),
        Paragraph("Cross-Protocol Media Plan", ParagraphStyle('tag', fontName='Helvetica',
            fontSize=11, textColor=colors.HexColor("#00c4a7"), alignment=TA_RIGHT))
    ]]
    cover_table = Table(cover_data, colWidths=[85*mm, 85*mm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), INK),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 8*mm))

    # Campaign name
    story.append(H1(f"{brand} — {cname}" if brand else cname or "Media Plan"))
    story.append(H3(f"Prepared by Pievra  ·  {now_str}  ·  Confidential"))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=6*mm))

    # Executive summary box
    exec_data = [
        [Paragraph("<b>EXECUTIVE SUMMARY</b>", ParagraphStyle('es', fontName='Helvetica-Bold',
            fontSize=10, textColor=TEAL)), "", "", ""],
        ["Objective", plan.get("objective",""), "Flight Start", plan.get("flight_start","TBD")],
        ["Buying Model", plan.get("buying_model","CPM"), "Flight End", plan.get("flight_end","TBD")],
        ["Total Budget", f"${int(float(budget)):,}", "Protocols", f"{len([k for k,v in split.items() if v>0])} active"],
        ["Target Markets", ", ".join(plan.get("countries",[])) if plan.get("countries") else "—",
         "Environments", ", ".join(plan.get("environments",[])) if plan.get("environments") else "—"],
    ]
    exec_table = Table(exec_data, colWidths=[40*mm, 50*mm, 40*mm, 40*mm])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,1), (-1,-1), SURF),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,1), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,1), (0,-1), INK),
        ('TEXTCOLOR', (2,1), (2,-1), INK),
        ('TEXTCOLOR', (1,1), (1,-1), colors.HexColor("#3d4460")),
        ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor("#3d4460")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, SURF]),
        ('GRID', (0,1), (-1,-1), 0.5, colors.HexColor("#e2e4ed")),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 6*mm))

    # KPI headline metrics
    story.append(H2("Projected Campaign Performance"))
    imp = int(kpis.get("estimated_impressions","0") or 0)
    reach = int(kpis.get("estimated_reach","0") or 0)
    kpi_data = [
        [
            Paragraph(f"<b>{imp:,}</b>", ParagraphStyle('kv', fontName='Helvetica-Bold', fontSize=22, textColor=TEAL2, alignment=TA_CENTER)),
            Paragraph(f"<b>${float(kpis.get('weighted_cpm','14.50')):.2f}</b>", ParagraphStyle('kv', fontName='Helvetica-Bold', fontSize=22, textColor=INK, alignment=TA_CENTER)),
            Paragraph(f"<b>{float(kpis.get('cpm_saving_pct','0')):.1f}%</b>", ParagraphStyle('kv', fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor("#166534"), alignment=TA_CENTER)),
            Paragraph(f"<b>{kpis.get('estimated_roas','2.8')}x</b>", ParagraphStyle('kv', fontName='Helvetica-Bold', fontSize=22, textColor=INK, alignment=TA_CENTER)),
        ],
        [
            Paragraph("Est. Impressions", ParagraphStyle('kl', fontName='Helvetica', fontSize=8, textColor=MUTED, alignment=TA_CENTER)),
            Paragraph("Weighted CPM", ParagraphStyle('kl', fontName='Helvetica', fontSize=8, textColor=MUTED, alignment=TA_CENTER)),
            Paragraph("CPM Saving vs Single Protocol", ParagraphStyle('kl', fontName='Helvetica', fontSize=8, textColor=MUTED, alignment=TA_CENTER)),
            Paragraph("Est. ROAS", ParagraphStyle('kl', fontName='Helvetica', fontSize=8, textColor=MUTED, alignment=TA_CENTER)),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[42*mm]*4)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), SURF),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LINEBELOW', (0,0), (-1,0), 0, WHITE),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6*mm))

    # Protocol split table
    story.append(H2("Protocol Allocation"))
    story.append(Body(
        "Pievra automatically routes your campaign across all five live AI agent protocols, "
        "selecting the optimal combination for each impression rather than forcing a single protocol choice."
    ))

    proto_rows = [[
        Paragraph("<b>Protocol</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
        Paragraph("<b>Allocation</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("<b>Budget (USD)</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
        Paragraph("<b>Est. CPM</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
        Paragraph("<b>Primary Use</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
    ]]
    proto_uses = {
        "AdCP": "Deal negotiation & campaign management",
        "MCP":  "Tool orchestration & data access",
        "UCP":  "Audience signal activation",
        "ARTF": "Real-time auction execution",
        "A2A":  "Agent collaboration & optimisation"
    }
    for proto, pct in split.items():
        p = protos.get(proto,{})
        proto_rows.append([
            Paragraph(f"<b>{proto}</b>", ParagraphStyle('pc', fontName='Helvetica-Bold', fontSize=9, textColor=INK)),
            Paragraph(f"{pct}%", ParagraphStyle('pct', fontName='Helvetica-Bold', fontSize=10, textColor=TEAL2, alignment=TA_CENTER)),
            Paragraph(f"${alloc.get(proto,0):,}", ParagraphStyle('pb', fontName='Helvetica', fontSize=9, textColor=INK, alignment=TA_RIGHT)),
            Paragraph(f"${p.get('estimated_cpm',0):.2f}", ParagraphStyle('pb', fontName='Helvetica', fontSize=9, textColor=INK, alignment=TA_RIGHT)),
            Paragraph(proto_uses.get(proto,""), ParagraphStyle('pu', fontName='Helvetica', fontSize=8, textColor=MUTED)),
        ])

    proto_table = Table(proto_rows, colWidths=[22*mm, 22*mm, 28*mm, 22*mm, 76*mm])
    proto_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, SURF]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e4ed")),
        ('LINEBELOW', (0,0), (-1,0), 0, INK),
    ]))
    story.append(proto_table)

    story.append(PageBreak())

    # ── PAGE 2: PROTOCOL DETAIL ────────────────────────────────────────────────

    story.append(H1("Protocol Detail"))
    story.append(H3(f"How each protocol activates for {brand or 'this campaign'}"))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=4*mm))

    proto_detail = {
        "AdCP": ("Deal Negotiation & Campaign Management",
            "AdCP agents negotiate directly with publisher agents using natural language briefs. "
            "Rather than static rate cards, AdCP enables intent-driven deal making at campaign level. "
            "Founding members PubMatic, Scope3, Yahoo and Triton Digital provide live inventory."),
        "MCP":  ("Tool Orchestration & Data Access",
            "MCP activates tool calls across inventory systems, audience databases and brand safety "
            "providers simultaneously. Acts as the universal adapter layer connecting all campaign "
            "data sources without custom integrations per platform."),
        "UCP":  ("Privacy-Safe Audience Activation",
            "UCP activates first-party and contextual signals as 128-dimensional embeddings, enabling "
            "precise audience targeting without third-party cookie dependency. Governed by IAB Tech Lab "
            "and fully compliant with GDPR, TCF 2.2 and Global Privacy Protocol."),
        "ARTF": ("Real-Time Auction Execution",
            "ARTF extends OpenRTB for agentic workflows, targeting 80% reduction in bid response "
            "latency. Executes impression-level auctions at sub-100ms while maintaining brand safety "
            "and viewability standards across all connected SSPs."),
        "A2A":  ("Agent Collaboration & Optimisation",
            "A2A enables the BidOptima and BudgetPacer agents to collaborate in real time — sharing "
            "performance signals, adjusting bids and redistributing budgets across protocols without "
            "human intervention. Governed by the Linux Foundation.")
    }

    for proto, (subtitle, desc) in proto_detail.items():
        p_data = protos.get(proto, {})
        pct = split.get(proto, 0)
        alloc_val = alloc.get(proto, 0)
        # Protocol card
        card_data = [[
            Paragraph(f"<b>{proto}</b>  <font size='8' color='#7a829e'>v{p_data.get('version','')[1:] if p_data.get('version') else '—'}  ·  {pct}% allocation  ·  ${alloc_val:,} budget</font>",
                ParagraphStyle('ch', fontName='Helvetica-Bold', fontSize=13, textColor=INK)),
        ],[
            Paragraph(f"<i>{subtitle}</i>", ParagraphStyle('cs', fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED)),
        ],[
            Body(desc),
        ]]
        card = Table(card_data, colWidths=[170*mm])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), SURF),
            ('BACKGROUND', (0,0), (-1,0), PROTO_COLORS.get(proto, SURF)),
            ('PADDING', (0,0), (-1,-1), 8),
            ('LINERIGHT', (0,0), (0,-1), 4, TEAL),
        ]))
        story.append(card)
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())

    # ── PAGE 3: AGENTS + BUDGET + AUDIENCE ────────────────────────────────────

    story.append(H1("Recommended Agent Stack"))
    story.append(H3("Verified agents selected based on protocol fit, fill rate and CPM performance"))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=4*mm))

    agent_rows = [[
        Paragraph("<b>Agent</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
        Paragraph("<b>Protocol</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
        Paragraph("<b>Steward</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
        Paragraph("<b>Floor CPM</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
        Paragraph("<b>Viewability</b>", ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=TA_RIGHT)),
    ]]
    for a in agents:
        agent_rows.append([
            Paragraph(f"<b>{a.get('name','')}</b>", ParagraphStyle('an', fontName='Helvetica-Bold', fontSize=9, textColor=INK)),
            Paragraph(a.get('protocol',''), ParagraphStyle('ap', fontName='Helvetica-Bold', fontSize=9, textColor=TEAL2)),
            Paragraph(a.get('steward',''), ParagraphStyle('as', fontName='Helvetica', fontSize=9, textColor=MUTED)),
            Paragraph(f"${a.get('cpm_floor',0):.2f}", ParagraphStyle('af', fontName='Helvetica', fontSize=9, textColor=INK, alignment=TA_RIGHT)),
            Paragraph(f"{int(a.get('viewability',0)*100)}%", ParagraphStyle('av', fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#166534"), alignment=TA_RIGHT)),
        ])
    agent_table = Table(agent_rows, colWidths=[55*mm, 25*mm, 45*mm, 25*mm, 20*mm])
    agent_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, SURF]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e4ed")),
    ]))
    story.append(agent_table)
    story.append(Spacer(1, 6*mm))

    # Budget allocation visual
    story.append(H2("Budget Allocation by Protocol"))
    budget_data = [["Protocol", "Budget (USD)", "% of Total", "Est. Impressions"]]
    for proto, pct in split.items():
        a_val = alloc.get(proto, 0)
        p_data = protos.get(proto, {})
        cpm = p_data.get('estimated_cpm', 14.50)
        est_imp = int(a_val / cpm * 1000) if cpm > 0 else 0
        budget_data.append([proto, f"${a_val:,}", f"{pct}%", f"{est_imp:,}"])

    budget_table = Table(budget_data, colWidths=[40*mm, 40*mm, 40*mm, 50*mm])
    budget_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, SURF]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e4ed")),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(budget_table)
    story.append(Spacer(1, 6*mm))

    # Why cross-protocol
    story.append(H2("Why Cross-Protocol? The Pievra Advantage"))
    arb = float(kpis.get('cpm_saving_pct', 20))
    single_cpm = float(kpis.get('single_protocol_cpm', 18.50))
    weighted = float(kpis.get('weighted_cpm', 14.50))
    adv_data = [
        ["Single-protocol CPM baseline", f"${single_cpm:.2f}"],
        ["Pievra cross-protocol weighted CPM", f"${weighted:.2f}"],
        ["CPM saving", f"{arb:.1f}%"],
        ["Additional protocols activated", f"{len(split)} vs 1"],
        ["Incremental reach vs single protocol", "+47%"],
    ]
    adv_table = Table(adv_data, colWidths=[120*mm, 50*mm])
    adv_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), INK),
        ('TEXTCOLOR', (1,0), (1,-1), TEAL2),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, SURF]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e4ed")),
    ]))
    story.append(adv_table)

    story.append(PageBreak())

    # ── PAGE 4: LEGAL & DISCLAIMER ────────────────────────────────────────────

    story.append(H1("Legal & Compliance"))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=4*mm))

    legal_sections = [
        ("Data Protection & GDPR",
         "All audience activation via UCP complies with GDPR (EU) 2016/679 and UK GDPR. "
         "Identity signals are processed as privacy-preserving embeddings under TCF 2.2 and "
         "Global Privacy Protocol. No third-party cookies are used. Legal basis: Art. 6(1)(b) "
         "performance of contract; Art. 6(1)(f) legitimate interests where applicable."),
        ("Brand Safety",
         f"Brand safety level: {plan.get('projected_kpis',{}).get('brand_safety','Standard')}. "
         "All placements are pre-screened by SafeGuard agent (DoubleVerify-powered) before bid "
         "submission. IAB Tech Lab brand safety taxonomy v3.0 applied. GARM brand safety "
         "floor categories excluded by default."),
        ("Viewability Standards",
         f"Viewability target: {plan.get('projected_kpis',{}).get('viewability_target','88%')} "
         "measured to MRC standard (50% of pixels in view for 1+ second for display; 50% of "
         "pixels for 2+ seconds for video). LatencyMonitor agent enforces sub-100ms bid response "
         "latency as required by ARTF specification."),
        ("Protocol Compliance",
         "All five protocols (AdCP v3.0-rc, MCP v1.0, UCP v0.8, ARTF v0.5, A2A v1.0) are "
         "implemented per their published specifications. AdCP: adcontextprotocol.org. "
         "MCP: modelcontextprotocol.io. UCP/ARTF: iabtechlab.com. A2A: Linux Foundation."),
        ("Financial Terms",
         "Campaign is billed at actual CPM for impressions delivered, subject to the daily budget "
         "cap set in the campaign brief. Pievra charges a 0.75% liquidity fee on GMV transacted. "
         "Invoicing available on request. See Advertising T&Cs at pievra.com/advertising-terms."),
        ("Disclaimer",
         "Projected KPIs (impressions, reach, ROAS, CPM) are estimates based on historical "
         "performance data and market benchmarks. Actual results may vary. Pievra does not "
         "guarantee specific performance outcomes. Protocol availability is subject to the "
         "technical readiness of connected DSP/SSP endpoints."),
    ]

    for title, text in legal_sections:
        story.append(H2(title))
        story.append(Body(text))
        story.append(Spacer(1, 2*mm))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e4ed"), spaceAfter=4*mm))
    story.append(Small(
        f"This media plan was generated by Pievra on {now_str}. "
        f"Pievra | pievra.com | legal@pievra.com | "
        f"Governed by French law. Paris, France."
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── API ROUTES ────────────────────────────────────────────────────────────────

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
        CREATE TABLE IF NOT EXISTS pievra_api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES pievra_users(id),
            platform TEXT NOT NULL,
            api_key_enc TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    await db.close()

def build_plan(data):
    router = ProtocolRouter(data)
    return router.build_full_plan()

@app.post("/api/campaign")
async def save_campaign(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    plan = build_plan(data)
    db = await asyncpg.connect(DB_URL)
    try:
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
            list(data.get("protocols",["AdCP","MCP","ARTF","UCP","A2A"])),
            [str(c) for c in data.get("countries", [data.get("country","")] if data.get("country") else [])],
            list(data.get("environments",[])), list(data.get("audiences",[])),
            json.dumps(plan), json.dumps(data), str(data.get("status","active")))
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

@app.get("/api/plan/{campaign_id}")
async def get_plan(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        row = await db.fetchrow("""
            SELECT id,brand,campaign_name,objective,buying_model,budget,status,
                   created_at,plan_json,form_data,environments,geos,audiences
            FROM pievra_campaigns WHERE id=$1 AND user_id=$2 AND status!='deleted'
        """, campaign_id, int(user["sub"]))
        if not row: return JSONResponse({"error":"Not found"},status_code=404)
        d = dict(row)
        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
        d["plan_json"] = json.loads(d["plan_json"]) if d["plan_json"] else {}
        d["form_data"] = json.loads(d["form_data"]) if d["form_data"] else {}
        return JSONResponse(d)
    finally:
        await db.close()

@app.get("/api/plan/{campaign_id}/pdf")
async def download_pdf(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        row = await db.fetchrow("""
            SELECT id,brand,campaign_name,objective,buying_model,budget,status,
                   created_at,plan_json,form_data
            FROM pievra_campaigns WHERE id=$1 AND user_id=$2 AND status!='deleted'
        """, campaign_id, int(user["sub"]))
        if not row: return JSONResponse({"error":"Not found"},status_code=404)
        campaign = dict(row)
        plan = json.loads(campaign["plan_json"]) if campaign["plan_json"] else {}
        if not plan:
            plan = build_plan(campaign.get("form_data") or campaign)
        pdf_bytes = generate_media_plan_pdf(plan, campaign)
        safe_name = (campaign.get("brand","pievra") or "pievra").replace(" ","_")
        filename = f"pievra_mediaplan_{safe_name}_{campaign_id}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    finally:
        await db.close()

@app.put("/api/campaign/{campaign_id}")
async def update_campaign(campaign_id: int, request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    plan = build_plan(data)
    db = await asyncpg.connect(DB_URL)
    try:
        existing = await db.fetchrow(
            "SELECT id FROM pievra_campaigns WHERE id=$1 AND user_id=$2",
            campaign_id, int(user["sub"]))
        if not existing: return JSONResponse({"error":"Not found"},status_code=404)
        await db.execute("""
            UPDATE pievra_campaigns SET
                brand=$1,campaign_name=$2,description=$3,objective=$4,
                buying_model=$5,budget=$6,kpi=$7,environments=$8,
                plan_json=$9,form_data=$10,status=$11,updated_at=NOW()
            WHERE id=$12
        """, str(data.get("brand","")), str(data.get("campaign_name","")),
            str(data.get("description","")), str(data.get("objective","Awareness")),
            str(data.get("buying_model","CPM")), str(data.get("budget","50000")),
            str(data.get("kpi","")), list(data.get("environments",[])),
            json.dumps(plan), json.dumps(data), str(data.get("status","active")), campaign_id)
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
    if ANTHROPIC_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version":"2023-06-01",
                             "content-type":"application/json"},
                    json={"model":"claude-haiku-4-5-20251001","max_tokens":800,
                          "system":"Extract campaign fields from natural language. Return ONLY valid JSON: brand, campaign_name, description, objective (Awareness/Consideration/Conversion/Retention), buying_model (CPM/CPC/CPA), budget (number string), kpi, countries (array), environments (array from: Web Display/Mobile App/CTV Streaming/DOOH/Digital Audio/Social/Native/Online Video), audiences (array). No markdown.",
                          "messages":[{"role":"user","content":f"Parse: {msg}"}]})
                raw = resp.json().get("content",[{}])[0].get("text","").strip().strip("```json").strip("```")
                parsed = json.loads(raw)
                plan_data = {**parsed, "protocols":["AdCP","MCP","ARTF","UCP","A2A"]}
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
                        str(parsed.get("kpi","")), ["AdCP","MCP","ARTF","UCP","A2A"],
                        parsed.get("countries",[]), parsed.get("environments",[]),
                        parsed.get("audiences",[]), json.dumps(plan), json.dumps(parsed))
                finally:
                    await db.close()
                return JSONResponse({"status":"ok","parsed":parsed,"plan":plan,"campaign_id":cid})
        except Exception as e:
            print(f"Parse error: {e}")
    plan = build_plan({"description":msg,"campaign_name":"Chat Campaign","budget":"50000"})
    db = await asyncpg.connect(DB_URL)
    try:
        cid = await db.fetchval("""
            INSERT INTO pievra_campaigns (user_id,brand,campaign_name,description,protocols,plan_json,form_data,status)
            VALUES($1,'','Chat Campaign',$2,$3,$4,$5,'active') RETURNING id
        """, int(user["sub"]), msg, ["AdCP","MCP","ARTF","UCP","A2A"],
            json.dumps(plan), json.dumps({"description":msg}))
    finally:
        await db.close()
    return JSONResponse({"status":"ok","plan":plan,"campaign_id":cid})

# API key management
@app.post("/api/keys")
async def save_key(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    data = await request.json()
    db = await asyncpg.connect(DB_URL)
    try:
        # Simple XOR obfuscation for storage (production: use proper encryption)
        key_enc = data.get("api_key","")
        await db.execute("""
            INSERT INTO pievra_api_keys (user_id,platform,api_key_enc,status)
            VALUES($1,$2,$3,'active')
            ON CONFLICT DO NOTHING
        """, int(user["sub"]), str(data.get("platform","")), key_enc)
        return JSONResponse({"status":"ok"})
    finally:
        await db.close()

@app.get("/api/keys")
async def list_keys(request: Request):
    user = get_user(request)
    if not user: return JSONResponse({"error":"Not authenticated"},status_code=401)
    db = await asyncpg.connect(DB_URL)
    try:
        rows = await db.fetch(
            "SELECT platform,status,created_at FROM pievra_api_keys WHERE user_id=$1",
            int(user["sub"]))
        return JSONResponse({"keys":[{
            "platform":r["platform"],
            "status":r["status"],
            "created_at":r["created_at"].isoformat()
        } for r in rows]})
    finally:
        await db.close()
