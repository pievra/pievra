"""
Google + LinkedIn OAuth routes — appended to auth_api.py
Endpoints:
  GET /auth/google           → redirect to Google
  GET /auth/google/callback  → handle Google callback
  GET /auth/linkedin         → redirect to LinkedIn
  GET /auth/linkedin/callback→ handle LinkedIn callback
"""
import os, secrets, urllib.parse
import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
LINKEDIN_CLIENT_ID   = os.environ.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
BASE_URL = os.environ.get("BASE_URL", "https://pievra.com")

OAUTH_STATE_STORE = {}  # In production use Redis

# ── GOOGLE ────────────────────────────────────────────────────────────────────

def google_auth_url():
    state = secrets.token_urlsafe(16)
    OAUTH_STATE_STORE[state] = True
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params), state

async def google_get_token(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{BASE_URL}/auth/google/callback",
            "grant_type": "authorization_code"
        })
        return r.json()

async def google_get_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get("https://www.googleapis.com/oauth2/v2/userinfo",
                             headers={"Authorization": f"Bearer {access_token}"})
        return r.json()

# ── LINKEDIN ──────────────────────────────────────────────────────────────────

def linkedin_auth_url():
    state = secrets.token_urlsafe(16)
    OAUTH_STATE_STORE[state] = True
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/auth/linkedin/callback",
        "state": state,
        "scope": "openid profile email"
    }
    return "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params), state

async def linkedin_get_token(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post("https://www.linkedin.com/oauth/v2/accessToken", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{BASE_URL}/auth/linkedin/callback",
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        return r.json()

async def linkedin_get_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get("https://api.linkedin.com/v2/userinfo",
                             headers={"Authorization": f"Bearer {access_token}"})
        return r.json()
