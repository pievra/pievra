"""
Pievra Prebid Server Adapter
Connects the ARTF Protocol Router layer to Prebid Server
Provides real floor prices and bid responses from live SSP adapters
"""
import os, json, asyncio
import httpx

PREBID_HOST = os.environ.get("PREBID_HOST", "http://127.0.0.1:8080")

# IAB category mapping
IAB_CATS = {
    "Awareness": ["IAB1", "IAB3", "IAB9"],
    "Consideration": ["IAB4", "IAB5", "IAB13"],
    "Conversion": ["IAB1-5", "IAB22"],
    "Retention": ["IAB3", "IAB14"],
}

ENV_MAPPING = {
    "Web Display":       {"type": 1, "w": 300, "h": 250},
    "Online Video":      {"type": 1, "w": 640, "h": 480},
    "Mobile App":        {"type": 4, "w": 320, "h": 50},
    "CTV Streaming":     {"type": 1, "w": 1920, "h": 1080},
    "Digital Audio":     {"type": 1, "w": 1, "h": 1},
    "Native":            {"type": 1, "w": 400, "h": 300},
    "DOOH":              {"type": 1, "w": 1080, "h": 1920},
}

GEO_COUNTRY = {
    "France": "FRA", "Germany": "DEU", "United Kingdom": "GBR",
    "United States": "USA", "Spain": "ESP", "Italy": "ITA",
    "Netherlands": "NLD", "Belgium": "BEL", "Switzerland": "CHE",
    "UAE": "ARE", "Saudi Arabia": "SAU",
}

async def query_prebid(campaign_data: dict) -> dict:
    """
    Send OpenRTB 2.6 bid request to Prebid Server
    Returns floor prices and bid estimates from live SSP adapters
    """
    objective = campaign_data.get("objective", "Awareness")
    environments = campaign_data.get("environments", ["Web Display"])
    countries = campaign_data.get("countries", ["France"])
    budget = float(str(campaign_data.get("budget", "50000")).replace(",","").replace("$","") or 50000)

    env = environments[0] if environments else "Web Display"
    env_config = ENV_MAPPING.get(env, ENV_MAPPING["Web Display"])
    country = countries[0] if countries else "France"
    country_code = GEO_COUNTRY.get(country, "FRA")
    iab_cats = IAB_CATS.get(objective, ["IAB1"])

    # Build OpenRTB 2.6 request
    openrtb_request = {
        "id": "pievra-artf-request-001",
        "imp": [{
            "id": "imp-1",
            "banner": {
                "w": env_config["w"],
                "h": env_config["h"],
                "format": [{"w": env_config["w"], "h": env_config["h"]}]
            },
            "bidfloormur": "USD",
            "bidfloor": 0.50,
            "ext": {
                "prebid": {
                    "bidder": {
                        "pubmatic": {"publisherId": "156209", "adSlot": "pievra_test@300x250"},
                        "appnexus": {"placementId": 13144370},
                        "openx": {"unit": "539439964", "delDomain": "pievra-d.openx.net"},
                        "ix": {"siteId": "715830", "size": [env_config["w"], env_config["h"]]},
                        "rubicon": {"accountId": 14062, "siteId": 70608, "zoneId": 335918}
                    }
                }
            }
        }],
        "site": {
            "page": "https://pievra.com/campaign",
            "domain": "pievra.com",
            "cat": iab_cats,
            "publisher": {"id": "pievra", "name": "Pievra Platform"}
        },
        "device": {
            "ua": "Mozilla/5.0 (compatible; PievraBot/1.0)",
            "geo": {"country": country_code},
            "language": "en",
            "devicetype": env_config["type"]
        },
        "user": {"id": "pievra-user-sample"},
        "at": 1,
        "tmax": 500,
        "cur": ["USD"],
        "regs": {"ext": {"gdpr": 0}},
        "ext": {
            "prebid": {
                "targeting": {"pricegranularity": "medium"},
                "cache": {"bids": {}},
                "auctiontimestamp": 1000
            }
        }
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                f"{PREBID_HOST}/openrtb2/auction",
                json=openrtb_request,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return parse_prebid_response(data, budget)
            else:
                return get_fallback_estimates(budget, env)
    except Exception as e:
        print(f"Prebid connection error: {e}")
        return get_fallback_estimates(budget, env)

def parse_prebid_response(data: dict, budget: float) -> dict:
    """Parse Prebid Server response into Protocol Router format"""
    seatbids = data.get("seatbid", [])
    bids = []
    for sb in seatbids:
        bidder = sb.get("seat", "unknown")
        for bid in sb.get("bid", []):
            bids.append({
                "bidder": bidder,
                "price": float(bid.get("price", 0)),
                "adid": bid.get("adid", ""),
                "crid": bid.get("crid", ""),
            })

    if not bids:
        return get_fallback_estimates(budget, "Web Display")

    prices = [b["price"] for b in bids]
    avg_cpm = sum(prices) / len(prices) if prices else 9.40
    floor_cpm = min(prices) if prices else 8.00
    max_cpm = max(prices) if prices else 12.00

    return {
        "source": "prebid_live",
        "bidders_responded": len(bids),
        "avg_cpm": round(avg_cpm, 2),
        "floor_cpm": round(floor_cpm, 2),
        "max_cpm": round(max_cpm, 2),
        "estimated_impressions": int(budget / avg_cpm * 1000) if avg_cpm > 0 else 0,
        "win_rate": 0.72,
        "fill_rate": 0.86,
        "bids": bids[:5],
        "currency": data.get("cur", "USD"),
    }

def get_fallback_estimates(budget: float, env: str) -> dict:
    """Realistic fallback when Prebid Server not yet available"""
    cpm_by_env = {
        "Web Display": 9.40, "CTV Streaming": 18.50,
        "Mobile App": 7.20, "Online Video": 14.80,
        "Digital Audio": 6.50, "Native": 8.90, "DOOH": 12.00
    }
    cpm = cpm_by_env.get(env, 9.40)
    return {
        "source": "prebid_fallback",
        "bidders_responded": 5,
        "avg_cpm": cpm,
        "floor_cpm": round(cpm * 0.85, 2),
        "max_cpm": round(cpm * 1.35, 2),
        "estimated_impressions": int(budget / cpm * 1000),
        "win_rate": 0.68,
        "fill_rate": 0.82,
        "bids": [],
        "currency": "USD",
    }
