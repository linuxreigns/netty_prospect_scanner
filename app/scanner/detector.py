import json
import re

from bs4 import BeautifulSoup

from .fingerprints import (
    CHATBOT_FINGERPRINTS,
    CMS_FINGERPRINTS,
    CONTACT_KEYWORDS,
    CRM_FORM_FINGERPRINTS,
    CTA_KEYWORDS,
    ECOMMERCE_FINGERPRINTS,
    ECOMMERCE_HINTS,
    FRONTEND_FINGERPRINTS,
    PARKED_PATTERNS,
    SOCIAL_PATTERNS,
    WHATSAPP_PATTERNS,
)

# ── Phone ────────────────────────────────────────────────────────────────────
# Panama numbers: 8 digits (XXXX-XXXX) with optional +507 prefix → max 11 digits
_PHONE_RE = re.compile(r"(?<!\d)" r"(\+?507[\s.\-]?)?" r"(\(507\)[\s.\-]?)?" r"(\d{3,4}[\s.\-]?\d{4})" r"(?!\d)")
_TEL_HREF_RE = re.compile(r"tel:[\s]*([+\d\s\-().]{7,20})")

# ── Email ─────────────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_EMAIL_SKIP_EXT = {"png", "jpg", "gif", "svg", "css", "js", "webp", "woff", "woff2", "ttf", "eot"}
# Platform/vendor domains that appear in site HTML but belong to the tool, not the business
_EMAIL_SKIP_DOMAINS = {
    "sentry.io",
    "starapps.studio",
    "shopify.com",
    "wordpress.com",
    "wix.com",
    "squarespace.com",
    "cloudflare.com",
    "google.com",
    "facebook.com",
    "example.com",
    "example.org",
    "yourdomain.com",
    "email.com",
    "domain.com",
    "mail.com",
    "test.com",
    "demo.com",
}

# ── WhatsApp ──────────────────────────────────────────────────────────────────
_WA_RE = re.compile(r"(?:wa\.me|api\.whatsapp\.com/send\?phone=|whatsapp://send\?phone=)[/=]?(\d{7,15})")

# ── Social URLs ───────────────────────────────────────────────────────────────
_SOCIAL_URL_RE = {
    "facebook_url": re.compile(
        r"https?://(?:www\.)?facebook\.com/"
        r"(?!sharer|share|dialog|plugins|login|help|groups|events|pages/create|tr/?[\"'\s]|2008|photo|video|watch|story)"
        r"([A-Za-z0-9][A-Za-z0-9._\-]{2,})"
    ),
    "instagram_url": re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{2,})/?(?!\bexplore\b|\bp\b|\btv\b)"),
    "linkedin_url": re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/([A-Za-z0-9._\-]{2,})/?"),
    "twitter_url": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/([A-Za-z0-9_]{2,})/?"),
    "youtube_url": re.compile(r"https?://(?:www\.)?youtube\.com/(?:channel/|c/|user/|@)([A-Za-z0-9_.\-]{2,})/?"),
    "tiktok_url": re.compile(r"https?://(?:www\.)?tiktok\.com/@([A-Za-z0-9._\-]{2,})/?"),
}

# ── Address ───────────────────────────────────────────────────────────────────
_ADDRESS_RE = re.compile(
    r"(?:calle|ave\.?|avenida|vía|via|urb\.?|urbanización|edificio|local|piso|torre|blvd\.?|boulevard|"
    r"corregimiento|corr\.?|corro\.?|costa del este|punta pacífica|marbella|obarrio|"
    r"via españa|via cincuentenario|tumba muerto|transistmica)"
    r"[^<\n\r]{5,80}",
    re.IGNORECASE,
)


def _contains_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def detect_technology(html: str, headers: dict, cookies: str = "") -> dict:
    blob = "\n".join([html or "", str(headers or {}), cookies or ""]).lower()

    cms = None
    for name, patterns in CMS_FINGERPRINTS.items():
        if _contains_any(blob, patterns):
            cms = name
            break

    ecommerce = None
    for name, patterns in ECOMMERCE_FINGERPRINTS.items():
        if _contains_any(blob, patterns):
            ecommerce = name
            break

    frontend = None
    for name, patterns in FRONTEND_FINGERPRINTS.items():
        if _contains_any(blob, patterns):
            frontend = name
            break

    if cms is None and frontend is None:
        if "<?php" in html.lower() or "x-powered-by': 'php" in blob or "x-powered-by: php" in blob:
            cms = "PHP genérico"
        else:
            cms = "HTML estático"

    return {"cms": cms, "ecommerce_platform": ecommerce, "frontend_stack": frontend}


# ── Schema.org / JSON-LD ──────────────────────────────────────────────────────


def _parse_schema_org(soup: BeautifulSoup) -> dict:
    """Extract structured contact/business data from JSON-LD blocks."""
    result: dict = {}
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        # Handle both single object and @graph array
        items = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            items = data["@graph"]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type", "")
            # LocalBusiness, Restaurant, Store, etc.
            if not any(k in str(t) for k in ["Business", "Restaurant", "Store", "Organization", "Hotel", "Service"]):
                continue
            if "name" not in result and item.get("name"):
                result["schema_name"] = str(item["name"])
            if "telephone" not in result and item.get("telephone"):
                result["schema_phone"] = str(item["telephone"])
            if "email" not in result and item.get("email"):
                result["schema_email"] = str(item["email"])
            if "url" not in result and item.get("url"):
                result["schema_url"] = str(item["url"])
            addr = item.get("address")
            if addr and "schema_address" not in result:
                if isinstance(addr, dict):
                    parts = [
                        addr.get("streetAddress", ""),
                        addr.get("addressLocality", ""),
                        addr.get("addressRegion", ""),
                    ]
                    combined = ", ".join(p for p in parts if p)
                    if combined:
                        result["schema_address"] = combined
                elif isinstance(addr, str) and addr:
                    result["schema_address"] = addr
            hours = item.get("openingHours") or item.get("openingHoursSpecification")
            if hours and "schema_hours" not in result:
                if isinstance(hours, list):
                    result["schema_hours"] = "; ".join(str(h) for h in hours[:5])
                elif isinstance(hours, str):
                    result["schema_hours"] = hours
            price = item.get("priceRange")
            if price and "schema_price_range" not in result:
                result["schema_price_range"] = str(price)
    return result


# ── Contact extraction helpers ────────────────────────────────────────────────


def _extract_phones(links: list[str], raw_text: str, schema_phone: str = "") -> str:
    seen: set[str] = set()
    hits: list[str] = []

    # Priority 1: Schema.org phone (most reliable)
    if schema_phone:
        digits = re.sub(r"\D", "", schema_phone)
        if 7 <= len(digits) <= 11 and digits not in seen:
            seen.add(digits)
            hits.append(schema_phone.strip())

    # Priority 2: tel: href links
    for href in links:
        if href and href.lower().startswith("tel:"):
            m = _TEL_HREF_RE.search(href.lower())
            if m:
                digits = re.sub(r"\D", "", m.group(1))
                if digits not in seen and 7 <= len(digits) <= 11:
                    seen.add(digits)
                    hits.append(m.group(1).strip())

    # Priority 3: regex on visible text (Panama numbers ≤ 11 digits)
    if not hits:
        for m in _PHONE_RE.finditer(raw_text):
            raw = m.group(0).strip()
            digits = re.sub(r"\D", "", raw)
            if digits not in seen and 7 <= len(digits) <= 11:
                seen.add(digits)
                hits.append(raw)
            if len(hits) >= 5:
                break

    return ", ".join(hits[:5])


def _extract_emails(links: list[str], html: str, site_domain: str = "", schema_email: str = "") -> str:
    seen: set[str] = set()
    hits: list[str] = []

    def _is_vendor(addr: str) -> bool:
        domain = addr.split("@")[-1] if "@" in addr else ""
        return domain in _EMAIL_SKIP_DOMAINS

    def _is_own_domain(addr: str) -> bool:
        """Prefer emails whose domain matches or is related to the site domain."""
        if not site_domain:
            return True
        domain = addr.split("@")[-1] if "@" in addr else ""
        base = site_domain.replace("www.", "").split(".")[0]
        return base in domain

    # Priority 1: Schema.org email
    if schema_email:
        addr = schema_email.strip().lower()
        if _EMAIL_RE.match(addr) and not _is_vendor(addr):
            seen.add(addr)
            hits.append(addr)

    # Priority 2: mailto: hrefs
    for href in links:
        if href and href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0].strip().lower()
            ext = addr.rsplit(".", 1)[-1] if "." in addr else ""
            if ext not in _EMAIL_SKIP_EXT and _EMAIL_RE.match(addr) and addr not in seen and not _is_vendor(addr):
                seen.add(addr)
                hits.append(addr)

    # Priority 3: regex on HTML — own-domain emails first, then others
    if not hits:
        own, other = [], []
        for m in _EMAIL_RE.finditer(html):
            addr = m.group(0).lower()
            ext = addr.rsplit(".", 1)[-1]
            if ext in _EMAIL_SKIP_EXT or addr in seen or _is_vendor(addr):
                continue
            seen.add(addr)
            (own if _is_own_domain(addr) else other).append(addr)
        hits = (own + other)[:5]

    return ", ".join(hits[:5])


def _extract_whatsapp(links: list[str], html: str) -> str:
    for lnk in links:
        if lnk and any(p in lnk.lower() for p in ["wa.me", "api.whatsapp", "whatsapp.com/send"]):
            m = _WA_RE.search(lnk)
            if m:
                return f"+{m.group(1)}"
    m = _WA_RE.search(html)
    if m:
        return f"+{m.group(1)}"
    return ""


def _extract_social_urls(html: str) -> dict[str, str]:
    results: dict[str, str] = {}
    for key, pattern in _SOCIAL_URL_RE.items():
        m = pattern.search(html)
        if m:
            results[key] = m.group(0)
    return results


def _extract_address(soup: BeautifulSoup, schema_address: str = "") -> str:
    if schema_address:
        return schema_address
    # Try itemprop="address" or class hints
    for tag in soup.find_all(attrs={"itemprop": "address"}):
        txt = tag.get_text(" ", strip=True)
        if 10 < len(txt) < 200:
            return txt
    # Regex on visible text
    text = soup.get_text(" ", strip=True)
    m = _ADDRESS_RE.search(text)
    if m:
        return m.group(0).strip()[:200]
    return ""


def _extract_business_name(soup: BeautifulSoup, schema_name: str = "") -> str:
    if schema_name:
        return schema_name
    og_name = soup.find("meta", property="og:site_name")
    if og_name and og_name.get("content"):
        return og_name["content"].strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)[:100]
    return ""


def _is_parked(title: str | None, text: str) -> bool:
    blob = f"{title or ''} {text[:500]}".lower()
    return any(p in blob for p in PARKED_PATTERNS)


# ── Main detection ────────────────────────────────────────────────────────────


def detect_signals(url: str, html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    raw_text = soup.get_text(" ", strip=True)
    links = [a.get("href", "") or "" for a in soup.find_all("a")]
    scripts_text = " ".join((s.get("src", "") or "") + " " + (s.text or "") for s in soup.find_all("script"))

    # Site domain from URL for email filtering
    from urllib.parse import urlparse

    site_domain = urlparse(url).netloc.replace("www.", "")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    meta_description = meta_desc_tag.get("content") if meta_desc_tag else None

    # OG metadata
    og_desc_tag = soup.find("meta", property="og:description")
    og_description = og_desc_tag.get("content") if og_desc_tag else None
    effective_description = meta_description or og_description

    # Schema.org / JSON-LD
    schema = _parse_schema_org(soup)

    # Contact extraction (schema → links → regex, in that order)
    phone_numbers = _extract_phones(links, raw_text, schema.get("schema_phone", ""))
    email_addresses = _extract_emails(links, html or "", site_domain, schema.get("schema_email", ""))
    whatsapp_number = _extract_whatsapp(links, html or "")
    address = _extract_address(soup, schema.get("schema_address", ""))
    business_name = _extract_business_name(soup, schema.get("schema_name", ""))

    has_email = bool(email_addresses)
    has_phone = bool(phone_numbers)

    has_whatsapp = any(any(p in (lnk or "").lower() for p in WHATSAPP_PATTERNS) for lnk in links) or _contains_any(
        text, WHATSAPP_PATTERNS
    )

    has_form = soup.find("form") is not None

    html_lower = (html or "").lower()
    has_facebook = "facebook.com" in html_lower
    has_instagram = "instagram.com" in html_lower

    social_urls = _extract_social_urls(html or "")

    has_contact_page = any(any(k in lnk.lower() for k in CONTACT_KEYWORDS) for lnk in links)
    has_products_or_cart = _contains_any(text, ECOMMERCE_HINTS) or _contains_any(
        " ".join(links).lower(), ECOMMERCE_HINTS
    )
    has_clear_cta = _contains_any(text, CTA_KEYWORDS)
    looks_outdated = bool(re.search(r"copyright\s*(19\d{2}|20(0\d|1[0-8]))", text))

    chatbot_vendor = None
    has_chatbot = False
    script_blob = f"{html_lower}\n{scripts_text.lower()}"
    for vendor, patterns in CHATBOT_FINGERPRINTS.items():
        if _contains_any(script_blob, patterns):
            chatbot_vendor = vendor
            has_chatbot = True
            break

    # SEO signals
    title_length = len(title) if title else 0
    meta_desc_length = len(effective_description) if effective_description else 0
    has_h1 = bool(soup.find_all("h1"))
    has_og_tags = bool(soup.find("meta", property=re.compile(r"^og:")))
    has_schema_markup = bool(schema)

    # Social networks
    social_hits: dict[str, bool] = {}
    for net, patterns in SOCIAL_PATTERNS.items():
        social_hits[net] = any(p in html_lower for p in patterns)
    has_tiktok = social_hits.get("tiktok", False) or bool(social_urls.get("tiktok_url"))
    has_youtube = social_hits.get("youtube", False) or bool(social_urls.get("youtube_url"))
    has_linkedin = social_hits.get("linkedin", False) or bool(social_urls.get("linkedin_url"))
    has_twitter = social_hits.get("twitter", False) or bool(social_urls.get("twitter_url"))
    social_count = sum([has_facebook, has_instagram, has_tiktok, has_youtube, has_linkedin, has_twitter])

    # CRM forms
    crm_form_vendor = None
    has_crm_form = False
    for vendor, patterns in CRM_FORM_FINGERPRINTS.items():
        if _contains_any(html_lower, patterns):
            crm_form_vendor = vendor
            has_crm_form = True
            break

    is_parked = _is_parked(title, text)

    return {
        "title": title,
        "meta_description": effective_description,
        "business_name": business_name or None,
        "address": address or None,
        "is_parked": is_parked,
        "has_chatbot": has_chatbot,
        "chatbot_vendor": chatbot_vendor,
        "has_whatsapp": has_whatsapp,
        "has_contact_form": has_form,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_facebook": has_facebook,
        "has_instagram": has_instagram,
        "has_contact_page": has_contact_page,
        "has_products_or_cart": has_products_or_cart,
        "looks_outdated": looks_outdated,
        "has_clear_cta": has_clear_cta,
        # Extracted contact data
        "phone_numbers": phone_numbers or None,
        "email_addresses": email_addresses or None,
        "whatsapp_number": whatsapp_number or None,
        **{k: v for k, v in social_urls.items()},
        # SEO
        "title_length": title_length,
        "meta_desc_length": meta_desc_length,
        "has_h1": has_h1,
        "has_og_tags": has_og_tags,
        "has_schema_markup": has_schema_markup,
        # Social
        "has_tiktok": has_tiktok,
        "has_youtube": has_youtube,
        "has_linkedin": has_linkedin,
        "has_twitter": has_twitter,
        "social_count": social_count,
        # CRM forms
        "has_crm_form": has_crm_form,
        "crm_form_vendor": crm_form_vendor,
        # Schema.org enrichment
        "schema_hours": schema.get("schema_hours") or None,
        "schema_price_range": schema.get("schema_price_range") or None,
    }
