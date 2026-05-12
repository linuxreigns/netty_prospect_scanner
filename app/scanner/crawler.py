import asyncio
import csv
import ipaddress
import random
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.scanner.detector import detect_signals, detect_technology
from app.scanner.playwright_fallback import fetch_rendered_html
from app.scanner.robots import can_fetch
from app.scoring.score_engine import compute_score

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

# Sub-pages to crawl when homepage lacks contact info
_CONTACT_SUBPAGES = ["/contacto", "/contact", "/contact-us", "/nosotros", "/about", "/ubicacion", "/donde-estamos"]


def _get_headers() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-PA,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


def _html_has_content(html: str) -> bool:
    """True if the page has enough visible text to be considered rendered."""
    soup = BeautifulSoup(html or "", "html.parser")
    return len(soup.get_text(" ", strip=True).split()) >= 60


def _needs_playwright(html: str, fetched: dict) -> bool:
    """
    Decide whether to try Playwright. Uses multiple signals beyond word count
    to handle Cloudflare-protected and JS-heavy sites that return large but
    contact-empty HTML responses.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    words = len(soup.get_text(" ", strip=True).split())

    # Always use Playwright for JS shells (empty first render)
    if words < 60:
        return True

    html_lower = (html or "").lower()
    resp_headers = fetched.get("headers", {})
    server = (resp_headers.get("server") or resp_headers.get("Server") or "").lower()
    is_cloudflare = "cloudflare" in server

    title_tag = soup.find("title")
    has_title = bool(title_tag and title_tag.get_text(strip=True))

    links = [a.get("href", "") or "" for a in soup.find_all("a")]
    has_contact_signal = any(any(k in lnk.lower() for k in ["tel:", "mailto:", "wa.me", "whatsapp"]) for lnk in links)
    has_social = any(s in html_lower for s in ["facebook.com", "instagram.com", "wa.me", "tiktok.com"])

    # Page has words but is missing key structure → likely a challenge or empty shell
    if not has_title and words < 600:
        return True

    # Cloudflare-protected AND no useful contact signals → Playwright can bypass
    if is_cloudflare and not has_contact_signal and not has_social:
        return True

    return False


def _has_contact_data(sig: dict) -> bool:
    """True if we already have useful contact info from the main page."""
    return bool(
        sig.get("phone_numbers")
        or sig.get("email_addresses")
        or sig.get("whatsapp_number")
        or sig.get("facebook_url")
        or sig.get("instagram_url")
    )


@dataclass
class ScanInput:
    url: str
    rubro: str | None = None
    provincia: str | None = None


def normalize_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return f"https://{url.strip()}"
    return url.strip()


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def _is_private_or_local_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast
    except ValueError:
        return True


def is_blocked_target(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return True
    if host.lower() in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        if _is_private_or_local_ip(info[4][0]):
            return True
    return False


def load_csv_urls(path: str) -> list[ScanInput]:
    rows: list[ScanInput] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url") or row.get("URL")
            if not url:
                continue
            rows.append(
                ScanInput(
                    url=normalize_url(url),
                    rubro=(row.get("rubro") or row.get("sector") or "").strip() or None,
                    provincia=(row.get("provincia") or "").strip() or None,
                )
            )
    return rows


def _fail_data(
    url: str,
    domain: str,
    item: ScanInput,
    ssl_enabled: bool,
    fail_reason: str,
    elapsed_ms: float | None = None,
) -> dict:
    data: dict = {
        "url": url,
        "domain": domain,
        "rubro": item.rubro,
        "provincia": item.provincia,
        "load_ok": False,
        "fail_reason": fail_reason,
        "http_code": None,
        "response_time_ms": elapsed_ms,
        "load_speed_tier": None,
        "ssl_enabled": ssl_enabled,
        "title": None,
        "meta_description": None,
        "business_name": None,
        "address": None,
        "cms": None,
        "ecommerce_platform": None,
        "frontend_stack": None,
        "has_chatbot": False,
        "chatbot_vendor": None,
        "has_whatsapp": False,
        "has_contact_form": False,
        "has_email": False,
        "has_phone": False,
        "has_facebook": False,
        "has_instagram": False,
        "has_contact_page": False,
        "has_products_or_cart": False,
        "looks_outdated": False,
        "has_clear_cta": False,
        "is_parked": False,
    }
    score, cls, reasons = compute_score(data)
    data.update(
        {"netty_fit_score": score, "fit_classification": cls, "score_reasons": " | ".join([fail_reason, *reasons])}
    )
    return data


async def _fetch(url: str, headers: dict, timeout: httpx.Timeout, verify: bool = True) -> dict:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(headers=headers, timeout=timeout, verify=verify) as client:
            r = await client.get(url, follow_redirects=True)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "ok": True,
            "status": r.status_code,
            "headers": dict(r.headers),
            "html": r.text,
            "url": str(r.url),
            "elapsed_ms": elapsed_ms,
            "cookies": "; ".join(f"{k}={v}" for k, v in r.cookies.items()),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "elapsed_ms": (time.perf_counter() - start) * 1000,
        }


async def _fetch_with_fallbacks(url: str, headers: dict, timeout: httpx.Timeout) -> dict:
    """Try HTTPS → HTTPS no-verify → HTTP, returning first success."""
    result = await _fetch(url, headers, timeout, verify=True)
    if result["ok"]:
        return result

    err = result.get("error", "")
    err_type = result.get("error_type", "")

    if "ssl" in err.lower() or "certificate" in err.lower() or "ConnectError" in err_type:
        result2 = await _fetch(url, headers, timeout, verify=False)
        if result2["ok"]:
            result2["ssl_bypass"] = True
            return result2

    if url.startswith("https://"):
        http_url = "http://" + url[8:]
        result3 = await _fetch(http_url, headers, timeout, verify=True)
        if result3["ok"]:
            result3["http_fallback"] = True
            return result3

    return result


def _merge_contact_signals(base: dict, extra: dict) -> None:
    """Fill missing contact fields in base dict from extra (sub-page signals)."""
    for field in [
        "phone_numbers",
        "email_addresses",
        "whatsapp_number",
        "facebook_url",
        "instagram_url",
        "tiktok_url",
        "youtube_url",
        "linkedin_url",
        "twitter_url",
        "address",
        "business_name",
        "schema_hours",
        "schema_price_range",
    ]:
        if not base.get(field) and extra.get(field):
            base[field] = extra[field]
    # Update booleans
    for field in [
        "has_phone",
        "has_email",
        "has_whatsapp",
        "has_facebook",
        "has_instagram",
        "has_contact_form",
        "has_schema_markup",
    ]:
        if extra.get(field):
            base[field] = True
    if extra.get("social_count", 0) > base.get("social_count", 0):
        base["social_count"] = extra["social_count"]


async def _enrich_from_subpages(base_url: str, headers: dict, timeout: httpx.Timeout) -> dict:
    """
    Try known contact sub-pages to extract missing contact data.
    Returns merged signals from the first sub-page that yields contact info.
    """
    for path in _CONTACT_SUBPAGES:
        sub_url = urljoin(base_url, path)
        fetched = await _fetch(sub_url, headers, timeout)
        if not fetched.get("ok") or fetched.get("status", 0) not in (200, 301, 302):
            continue
        html = fetched.get("html", "")
        if not html or len(html.strip()) < 200:
            continue
        sig = detect_signals(url=sub_url, html=html)
        if _has_contact_data(sig):
            return sig
    return {}


async def scan_one(item: ScanInput, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        await asyncio.sleep(settings.delay_seconds)

        url = normalize_url(item.url)
        domain = extract_domain(url)
        ssl_enabled = url.startswith("https://")

        if is_blocked_target(url):
            return _fail_data(url, domain, item, ssl_enabled, "ssrf_blocked")

        if settings.respect_robots_txt and not can_fetch(url, settings.user_agent):
            return _fail_data(url, domain, item, ssl_enabled, "robots_disallowed")

        headers = _get_headers()
        timeout = httpx.Timeout(settings.request_timeout_seconds)
        fetched = await _fetch_with_fallbacks(url, headers, timeout)

        if not fetched.get("ok"):
            err = fetched.get("error", "fetch_error")
            if "Name or service not known" in err or "getaddrinfo" in err:
                reason = "dns_error"
            elif "timed out" in err.lower() or "timeout" in err.lower():
                reason = "timeout"
            elif "ssl" in err.lower() or "certificate" in err.lower():
                reason = "ssl_error"
            elif "Connection refused" in err:
                reason = "connection_refused"
            else:
                reason = f"fetch_error: {err[:80]}"
            return _fail_data(url, domain, item, ssl_enabled, reason, fetched.get("elapsed_ms"))

        html = fetched.get("html", "")

        # Smart Playwright trigger: word count + Cloudflare + missing structure
        if settings.enable_playwright_fallback and _needs_playwright(html, fetched):
            pw = await asyncio.to_thread(fetch_rendered_html, url, settings.playwright_timeout_ms)
            if pw.get("ok") and pw.get("html") and _html_has_content(pw["html"]):
                html = pw["html"]

        tech = detect_technology(html=html, headers=fetched.get("headers", {}), cookies=fetched.get("cookies", ""))
        sig = detect_signals(url=url, html=html)

        # Sub-page enrichment: if homepage lacks contact data, crawl /contacto etc.
        if not _has_contact_data(sig):
            extra = await _enrich_from_subpages(url, headers, timeout)
            if extra:
                _merge_contact_signals(sig, extra)

        elapsed_ms = fetched.get("elapsed_ms") or 0
        if elapsed_ms < 1000:
            speed_tier = "fast"
        elif elapsed_ms < 2500:
            speed_tier = "ok"
        elif elapsed_ms < 5000:
            speed_tier = "slow"
        else:
            speed_tier = "very_slow"

        data = {
            "url": url,
            "domain": domain,
            "rubro": item.rubro,
            "provincia": item.provincia,
            "load_ok": True,
            "fail_reason": None,
            "http_code": fetched.get("status"),
            "response_time_ms": elapsed_ms,
            "load_speed_tier": speed_tier,
            "ssl_enabled": ssl_enabled,
            "ssl_bypass": fetched.get("ssl_bypass", False),
            "http_fallback": fetched.get("http_fallback", False),
            **tech,
            **sig,
        }

        score, cls, reasons = compute_score(data)
        data.update({"netty_fit_score": score, "fit_classification": cls, "score_reasons": " | ".join(reasons)})
        return data


async def scan_batch(items: list[ScanInput]) -> list[dict]:
    semaphore = asyncio.Semaphore(settings.max_concurrency)
    tasks = [scan_one(item, semaphore) for item in items]
    return await asyncio.gather(*tasks)
