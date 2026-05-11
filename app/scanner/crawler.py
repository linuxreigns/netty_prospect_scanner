import asyncio
import csv
import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.scanner.detector import detect_signals, detect_technology
from app.scanner.playwright_fallback import fetch_rendered_html
from app.scanner.robots import can_fetch
from app.scoring.score_engine import compute_score


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

    host_l = host.lower()
    if host_l in {"localhost", "127.0.0.1", "::1"}:
        return True

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False

    for info in infos:
        ip = info[4][0]
        if _is_private_or_local_ip(ip):
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
    url: str, domain: str, item: ScanInput, ssl_enabled: bool, fail_reason: str, elapsed_ms: float | None = None
) -> dict:
    """Return a minimal failed-scan data dict with score applied."""
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

    # SSL error → retry without verification
    if "ssl" in err.lower() or "certificate" in err.lower() or "ConnectError" in err_type:
        result2 = await _fetch(url, headers, timeout, verify=False)
        if result2["ok"]:
            result2["ssl_bypass"] = True
            return result2

    # HTTPS failed → try HTTP (only if original was https)
    if url.startswith("https://"):
        http_url = "http://" + url[8:]
        result3 = await _fetch(http_url, headers, timeout, verify=True)
        if result3["ok"]:
            result3["http_fallback"] = True
            return result3

    return result  # all fallbacks failed, return original error


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

        headers = {"User-Agent": settings.user_agent}
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

        # Playwright fallback for JS-heavy sites
        if settings.enable_playwright_fallback and len((html or "").strip()) < 1000:
            pw = fetch_rendered_html(url, timeout_ms=settings.playwright_timeout_ms)
            if pw.get("ok") and pw.get("html"):
                html = pw["html"]

        tech = detect_technology(html=html, headers=fetched.get("headers", {}), cookies=fetched.get("cookies", ""))
        sig = detect_signals(url=url, html=html)

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
