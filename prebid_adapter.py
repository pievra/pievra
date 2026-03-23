"""
Pievra Prebid Server Adapter v2
Connects ARTF Protocol Router to Prebid Server with live SSP bids
"""
import os, json
import httpx

PREBID_HOST = os.environ.get("PREBID_HOST", "http://127.0.0.1:8080")

ENV_SIZES = {
    "Web Display":    {"w": 300, "h": 250},
    "Online Video":   {"w": 640, "h": 480},
    "Mobile App":     {"w": 320, "h": 50},
    "CTV Streaming":  {"w": 1920, "h": 1080},
    "Digital Audio":  {"w": 1, "h": 1},
    "Native":         {"w": 400, "h": 300},
    "DOOH":           {"w": 1080, "h": 1920},
}

GEO_COUNTRY = {
    "France": "FRA", "Germany": "DEU", "United Kingdom": "GBR",
    "United States": "USA", "Spain": "ESP", "Italy": "ITA",
    "Netherlands": "NLD", "Belgium": "BEL", "Switzerland": "CHE",
    "UAE": "ARE", "Saudi Arabia": "SAU",
}

FALLBACK_CPM = {
    "Web Display": 9.40, "CTV Streaming": 18.50, "Mobile App": 7.20,
    "Online Video": 14.80, "Digital Audio": 6.50, "Native": 8.90, "DOOH": 12.00
}

async def query_prebid(campaign_data: dict) -> dict:
    environments = campaign_data.get("environments", ["Web Display"])
    countries = campaign_data.get("countries", ["France"])
    budget = float(str(campaign_data.get("budget","50000")).replace(",","").replace("$","") or 50000)
    env = environments[0] if environments else "Web Display"
    country = countries[0] if countries else "France"
    size = ENV_SIZES.get(env, ENV_SIZES["Web Display"])
    country_code = GEO_COUNTRY.get(country, "FRA")

    payload = {
        "id": "pievra-artf-001",
        "imp": [{
            "id": "i1",
            "banner": {"w": size["w"], "h": size["h"], "format": [{"w": size["w"], "h": size["h"]}]},
            "bidfloor": 0.50,
            "bidfloormur": "USD",
            "ext": {"prebid": {"bidder": {
                "appnexus": {"placementId": 13144370},
                "pubmatic": {"publisherId": "156209", "adSlot": "pievra@"+str(size["w"])+"x"+str(size["h"])},
                "openx": {"unit": "539439964", "delDomain": "pievra-d.openx.net"},
            }}}
        }],
        "site": {
            "page": "https://pievra.com/",
            "domain": "pievra.com",
            "publisher": {"id": "pievra", "name": "Pievra Platform"}
        },
        "device": {"geo": {"country": country_code}, "language": "en"},
        "tmax": 2000,
        "at": 1,
        "cur": ["USD"]
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                f"{PREBID_HOST}/openrtb2/auction",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                return parse_prebid_response(resp.json(), budget, env)
            else:
                print(f"Prebid error {resp.status_code}: {resp.text[:200]}")
                return get_fallback_estimates(budget, env)
    except Exception as e:
        print(f"Prebid connection error: {e}")
        return get_fallback_estimates(budget, env)

def parse_prebid_response(data: dict, budget: float, env: str) -> dict:
    bids = []
    for sb in data.get("seatbid", []):
        bidder = sb.get("seat", "unknown")
        for bid in sb.get("bid", []):
            price = float(bid.get("price", 0))
            if price > 0:
                bids.append({"bidder": bidder, "price": price})

    if not bids:
        return get_fallback_estimates(budget, env)

    prices = [b["price"] for b in bids]
    avg_cpm = round(sum(prices) / len(prices), 2)
    floor_cpm = round(min(prices) * 0.85, 2)
    max_cpm = round(max(prices) * 1.15, 2)

    return {
        "source": "prebid_live",
        "bidders_responded": len(bids),
        "avg_cpm": avg_cpm,
        "floor_cpm": floor_cpm,
        "max_cpm": max_cpm,
        "estimated_impressions": int(budget / avg_cpm * 1000) if avg_cpm > 0 else 0,
        "win_rate": 0.72,
        "fill_rate": 0.86,
        "bids": bids,
        "currency": data.get("cur", ["USD"])[0] if isinstance(data.get("cur"), list) else "USD",
    }

def get_fallback_estimates(budget: float, env: str) -> dict:
    cpm = FALLBACK_CPM.get(env, 9.40)
    return {
        "source": "prebid_fallback",
        "bidders_responded": 0,
        "avg_cpm": cpm,
        "floor_cpm": round(cpm * 0.85, 2),
        "max_cpm": round(cpm * 1.35, 2),
        "estimated_impressions": int(budget / cpm * 1000),
        "win_rate": 0.68,
        "fill_rate": 0.82,
        "bids": [],
        "currency": "USD",
    }
