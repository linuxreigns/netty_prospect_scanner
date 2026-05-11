import re

from bs4 import BeautifulSoup

from .fingerprints import (
    CHATBOT_FINGERPRINTS,
    CMS_FINGERPRINTS,
    CONTACT_KEYWORDS,
    CTA_KEYWORDS,
    ECOMMERCE_FINGERPRINTS,
    ECOMMERCE_HINTS,
    FRONTEND_FINGERPRINTS,
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


def detect_signals(url: str, html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    links = [a.get("href", "") for a in soup.find_all("a")]
    scripts_text = " ".join((s.get("src", "") or "") + " " + (s.text or "") for s in soup.find_all("script"))

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    meta_desc = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    meta_description = meta_desc.get("content") if meta_desc else None

    has_whatsapp = any(any(p in (lnk or "").lower() for p in WHATSAPP_PATTERNS) for lnk in links) or _contains_any(
        text, WHATSAPP_PATTERNS
    )
    has_form = soup.find("form") is not None

    email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    phone_regex = re.compile(r"(\+?507[\s-]?)?(\d{4}[\s-]?\d{4})")
    has_email = bool(email_regex.search(html or ""))
    has_phone = bool(phone_regex.search(text))

    has_facebook = "facebook.com" in (html or "").lower()
    has_instagram = "instagram.com" in (html or "").lower()

    has_contact_page = any(any(k in (lnk or "").lower() for k in CONTACT_KEYWORDS) for lnk in links)
    has_products_or_cart = _contains_any(text, ECOMMERCE_HINTS) or _contains_any(
        " ".join(links).lower(), ECOMMERCE_HINTS
    )
    has_clear_cta = _contains_any(text, CTA_KEYWORDS)

    looks_outdated = bool(re.search(r"copyright\s*(19\d{2}|20(0\d|1[0-8]))", text))

    chatbot_vendor = None
    has_chatbot = False
    script_blob = f"{html}\n{scripts_text}".lower()
    for vendor, patterns in CHATBOT_FINGERPRINTS.items():
        if _contains_any(script_blob, patterns):
            chatbot_vendor = vendor
            has_chatbot = True
            break

    return {
        "title": title,
        "meta_description": meta_description,
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
    }
