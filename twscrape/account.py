import json
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime

from httpx import AsyncClient, AsyncHTTPTransport

from .models import JSONTrait
from .utils import utc

TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"


@dataclass
class Account(JSONTrait):
    username: str
    password: str
    email: str
    email_password: str
    user_agent: str
    active: bool
    locks: dict[str, datetime] = field(default_factory=dict)  # queue: datetime
    stats: dict[str, int] = field(default_factory=dict)  # queue: requests
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    mfa_code: str | None = None
    proxy: str | None = None
    error_msg: str | None = None
    last_used: datetime | None = None
    error_history: list[datetime] = field(default_factory=list)  # timestamps of errors
    reactivation_priority: int = 0  # higher = more urgent to reactivate
    _tx: str | None = None

    @staticmethod
    def from_rs(rs: sqlite3.Row):
        doc = dict(rs)
        doc["locks"] = {k: utc.from_iso(v) for k, v in json.loads(doc["locks"]).items()}
        doc["stats"] = {k: v for k, v in json.loads(doc["stats"]).items() if isinstance(v, int)}
        doc["headers"] = json.loads(doc["headers"])
        doc["cookies"] = json.loads(doc["cookies"])
        doc["active"] = bool(doc["active"])
        doc["last_used"] = utc.from_iso(doc["last_used"]) if doc["last_used"] else None
        doc["error_history"] = [utc.from_iso(ts) for ts in json.loads(doc.get("error_history", "[]"))]
        doc["reactivation_priority"] = doc.get("reactivation_priority", 0)
        return Account(**doc)

    def to_rs(self):
        rs = asdict(self)
        rs["locks"] = json.dumps(rs["locks"], default=lambda x: x.isoformat())
        rs["stats"] = json.dumps(rs["stats"])
        rs["headers"] = json.dumps(rs["headers"])
        rs["cookies"] = json.dumps(rs["cookies"])
        rs["last_used"] = rs["last_used"].isoformat() if rs["last_used"] else None
        rs["error_history"] = json.dumps([ts.isoformat() for ts in rs["error_history"]])
        return rs

    def make_client(self, proxy: str | None = None) -> AsyncClient:
        proxies = [proxy, os.getenv("TWS_PROXY"), self.proxy]
        proxies = [x for x in proxies if x is not None]
        proxy = proxies[0] if proxies else None

        transport = AsyncHTTPTransport(retries=3)
        client = AsyncClient(proxy=proxy, follow_redirects=True, transport=transport)

        # CRITICAL: Only set essential cookies - other cookies (twid, guest_id, kdt, etc.)
        # cause 404 responses on endpoints like UserTweetsAndReplies
        if "auth_token" in self.cookies:
            client.cookies.set("auth_token", self.cookies["auth_token"])
        if "ct0" in self.cookies:
            client.cookies.set("ct0", self.cookies["ct0"])

        # Apply any saved headers
        client.headers.update(self.headers)

        # Default Twitter API settings
        client.headers["user-agent"] = self.user_agent
        client.headers["content-type"] = "application/json"
        client.headers["authorization"] = TOKEN
        client.headers["x-twitter-active-user"] = "yes"
        client.headers["x-twitter-auth-type"] = "OAuth2Session"
        client.headers["x-twitter-client-language"] = "en"

        # Browser fingerprint headers - required to avoid 404 on some endpoints
        client.headers["accept"] = "*/*"
        client.headers["accept-language"] = "en-US,en;q=0.9"
        client.headers["sec-ch-ua"] = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
        client.headers["sec-ch-ua-mobile"] = "?0"
        client.headers["sec-ch-ua-platform"] = '"macOS"'
        client.headers["sec-fetch-dest"] = "empty"
        client.headers["sec-fetch-mode"] = "cors"
        client.headers["sec-fetch-site"] = "same-origin"
        client.headers["priority"] = "u=1, i"

        if "ct0" in self.cookies:
            client.headers["x-csrf-token"] = self.cookies["ct0"]

        return client
