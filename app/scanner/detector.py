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


# --- Phone extraction ---
_PHONE_RE = re.compile(r"(?<!\d)" r"(\+?507[\s.\-]?)?" r"(\(507\)[\s.\-]?)?" r"(\d{3,4}[\s.\-]?\d{4})" r"(?!\d)")
_TEL_HREF_RE = re.compile(r"tel:[\s]*([+\d\s\-().]{7,20})")

# --- Email extraction ---
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_EMAIL_SKIP_EXT = {"png", "jpg", "gif", "svg", "css", "js", "webp", "woff", "woff2", "ttf", "eot"}

# --- WhatsApp extraction ---
_WA_RE = re.compile(r"(?:wa\.me|api\.whatsapp\.com/send\?phone=|whatsapp://send\?phone=)[/=]?(\d{7,15})")

# --- Social URL extraction ---
_SOCIAL_URL_RE = {
    "facebook_url": re.compile(
        r"https?://(?:www\.)?facebook\.com/"
        r"(?!sharer|share|dialog|plugins|login|help|groups|events|pages/create|tr/?$|2008|photo|video|watch|story)"
        r"([A-Za-z0-9][A-Za-z0-9._\-]{2,})"
    ),
    "instagram_url": re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{2,})/?(?!\bexplore\b|\bp\b|\btv\b)"),
    "linkedin_url": re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/([A-Za-z0-9._\-]{2,})/?"),
    "twitter_url": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/([A-Za-z0-9_]{2,})/?"),
    "youtube_url": re.compile(r"https?://(?:www\.)?youtube\.com/(?:channel/|c/|user/|@)([A-Za-z0-9_.\-]{2,})/?"),
}


def _extract_phones(links: list[str], raw_text: str) -> str:
    """Extract phones: prefer tel: hrefs (reliable), then regex on visible text."""
    seen: set[str] = set()
    hits: list[str] = []

    # 1. tel: links (most reliable)
    for href in links:
        if href and href.lower().startswith("tel:"):
            m = _TEL_HREF_RE.search(href.lower())
            if m:
                digits = re.sub(r"\D", "", m.group(1))
                if digits not in seen and 7 <= len(digits) <= 15:
                    seen.add(digits)
                    hits.append(m.group(1).strip())

    # 2. regex on visible text as fallback
    if not hits:
        for m in _PHONE_RE.finditer(raw_text):
            raw = m.group(0).strip()
            digits = re.sub(r"\D", "", raw)
            if digits not in seen and 7 <= len(digits) <= 15:
                seen.add(digits)
                hits.append(raw)
            if len(hits) >= 5:
                break

    return ", ".join(hits[:5])


def _extract_emails(links: list[str], html: str) -> str:
    """Extract emails: prefer mailto: hrefs (reliable), then regex on HTML."""
    seen: set[str] = set()
    hits: list[str] = []

    # 1. mailto: links (most reliable)
    for href in links:
        if href and href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0].strip().lower()
            ext = addr.rsplit(".", 1)[-1] if "." in addr else ""
            if ext not in _EMAIL_SKIP_EXT and _EMAIL_RE.match(addr) and addr not in seen:
                seen.add(addr)
                hits.append(addr)

    # 2. regex on HTML as fallback
    if not hits:
        for m in _EMAIL_RE.finditer(html):
            addr = m.group(0).lower()
            ext = addr.rsplit(".", 1)[-1]
            if ext not in _EMAIL_SKIP_EXT and addr not in seen:
                seen.add(addr)
                hits.append(addr)
            if len(hits) >= 5:
                break

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


def _is_parked(title: str | None, text: str) -> bool:
    blob = f"{title or ''} {text[:500]}".lower()
    return any(p in blob for p in PARKED_PATTERNS)


def detect_signals(url: str, html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    raw_text = soup.get_text(" ", strip=True)
    links = [a.get("href", "") or "" for a in soup.find_all("a")]
    scripts_text = " ".join((s.get("src", "") or "") + " " + (s.text or "") for s in soup.find_all("script"))

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    meta_desc = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    meta_description = meta_desc.get("content") if meta_desc else None

    has_whatsapp = any(any(p in (lnk or "").lower() for p in WHATSAPP_PATTERNS) for lnk in links) or _contains_any(
        text, WHATSAPP_PATTERNS
    )

    has_form = soup.find("form") is not None

    phone_numbers = _extract_phones(links, raw_text)
    email_addresses = _extract_emails(links, html or "")
    whatsapp_number = _extract_whatsapp(links, html or "")

    has_email = bool(email_addresses)
    has_phone = bool(phone_numbers)

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
    meta_desc_length = len(meta_description) if meta_description else 0
    has_h1 = bool(soup.find_all("h1"))
    has_og_tags = bool(soup.find("meta", property=re.compile(r"^og:")))
    has_schema_markup = '"@context"' in (html or "") and "schema.org" in html_lower

    # Social networks
    social_hits: dict[str, bool] = {}
    for net, patterns in SOCIAL_PATTERNS.items():
        social_hits[net] = any(p in html_lower for p in patterns)
    has_tiktok = social_hits.get("tiktok", False)
    has_youtube = social_hits.get("youtube", False)
    has_linkedin = social_hits.get("linkedin", False)
    has_twitter = social_hits.get("twitter", False)
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
        "meta_description": meta_description,
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
    }
