"""Google Docs utilities for fetching document content by tabs."""

import json
import re
import time
import aiohttp
import jwt
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).parent.parent / "google_credentials.json"

def extract_doc_id(url: str) -> str | None:
    """Extract Google Doc ID from a URL."""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

def make_tab_url(doc_url: str, tab_id: str) -> str:
    """Create a direct link to a specific tab in a Google Doc."""
    doc_id = extract_doc_id(doc_url)
    return f"https://docs.google.com/document/d/{doc_id}/edit?tab={tab_id}"

async def _get_access_token() -> tuple[str | None, str | None]:
    """Get OAuth2 access token using service account credentials."""
    if not CREDENTIALS_FILE.exists():
        return None, f"Service account file not found at {CREDENTIALS_FILE}"
    try:
        creds = json.loads(CREDENTIALS_FILE.read_text())
    except json.JSONDecodeError:
        return None, "Invalid JSON in credentials file"

    now = int(time.time())
    payload = {
        "iss": creds["client_email"],
        "scope": "https://www.googleapis.com/auth/documents.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }
    signed_jwt = jwt.encode(payload, creds["private_key"], algorithm="RS256")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://oauth2.googleapis.com/token",
            data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": signed_jwt},
        ) as resp:
            data = await resp.json()
            if "access_token" in data:
                return data["access_token"], None
            return None, f"Token error: {data.get('error_description', data)}"

async def fetch_google_doc(doc_id: str) -> tuple[dict | None, str | None]:
    """Fetch a Google Doc with all tabs. Returns (doc, error) tuple."""
    token, error = await _get_access_token()
    if error:
        return None, error

    url = f"https://docs.googleapis.com/v1/documents/{doc_id}?includeTabsContent=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return data, None
                error = data.get("error", {})
                code = error.get("code", resp.status)
                message = error.get("message", "Unknown error")
                if code == 403:
                    return None, f"Access denied ({code}): {message}. Share the doc with the service account email."
                elif code == 404:
                    return None, f"Document not found ({code}). Check that the URL is correct."
                else:
                    return None, f"Google API error ({code}): {message}"
    except aiohttp.ClientError as e:
        return None, f"Network error: {e}"

def parse_doc_tabs(doc: dict, doc_url: str) -> list[tuple[str, str, str]]:
    """Parse Google Doc tabs. Returns list of (title, tab_id, tab_url) tuples."""
    tabs = doc.get("tabs", [])
    results = []
    for tab in tabs:
        title = tab.get("tabProperties", {}).get("title", "Untitled")
        tab_id = tab.get("tabProperties", {}).get("tabId", "")
        tab_url = make_tab_url(doc_url, tab_id)
        results.append((title, tab_id, tab_url))
    return results
