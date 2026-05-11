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

    html_lower = (html or "").lower()
    has_facebook = "facebook.com" in html_lower
    has_instagram = "instagram.com" in html_lower

    has_contact_page = any(any(k in (lnk or "").lower() for k in CONTACT_KEYWORDS) for lnk in links)
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
    h1_tags = soup.find_all("h1")
    has_h1 = len(h1_tags) > 0
    has_og_tags = bool(soup.find("meta", property=re.compile(r"^og:")))
    has_schema_markup = '"@context"' in (html or "") and "schema.org" in html_lower

    # Additional social networks
    social_hits: dict[str, bool] = {}
    for net, patterns in SOCIAL_PATTERNS.items():
        social_hits[net] = any(p in html_lower for p in patterns)
    has_tiktok = social_hits.get("tiktok", False)
    has_youtube = social_hits.get("youtube", False)
    has_linkedin = social_hits.get("linkedin", False)
    has_twitter = social_hits.get("twitter", False)
    social_count = sum([has_facebook, has_instagram, has_tiktok, has_youtube, has_linkedin, has_twitter])

    # CRM-integrated forms
    crm_form_vendor = None
    has_crm_form = False
    for vendor, patterns in CRM_FORM_FINGERPRINTS.items():
        if _contains_any(html_lower, patterns):
            crm_form_vendor = vendor
            has_crm_form = True
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
