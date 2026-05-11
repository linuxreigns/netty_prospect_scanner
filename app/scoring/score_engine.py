from .sectors import HIGH_DEMAND_SECTORS


def clamp(value: int, min_v: int = 0, max_v: int = 100) -> int:
    return max(min_v, min(max_v, value))


def classify(score: int) -> str:
    if 80 <= score <= 100:
        return "Caliente"
    if 60 <= score <= 79:
        return "Bueno"
    if 40 <= score <= 59:
        return "Medio"
    return "Bajo"


def compute_score(data: dict) -> tuple[int, str, list[str]]:
    if not data.get("load_ok", False):
        base = min(20, data.get("netty_fit_score", 0) or 20)
        return base, classify(base), ["Sitio caído o inaccesible: score máximo 20"]

    score = 0
    reasons = []

    if not data.get("has_chatbot"):
        score += 25
        reasons.append("No tiene chatbot (+25)")
    else:
        score -= 25
        reasons.append("Ya tiene chatbot (-25)")

    if data.get("has_whatsapp"):
        score += 15
        reasons.append("Tiene WhatsApp (+15)")

    if data.get("has_contact_form"):
        score += 10
        reasons.append("Tiene formulario (+10)")

    if data.get("ecommerce_platform") or data.get("has_products_or_cart"):
        score += 20
        reasons.append("Tiene eCommerce o señales de compra (+20)")

    cms = (data.get("cms") or "").lower()
    ecommerce = (data.get("ecommerce_platform") or "").lower()
    if "wordpress" in cms or "woocommerce" in ecommerce:
        score += 15
        reasons.append("Usa WordPress/WooCommerce (+15)")

    if any(x in (cms + " " + ecommerce) for x in ["shopify", "magento", "prestashop"]):
        score += 12
        reasons.append("Usa Shopify/Magento/PrestaShop (+12)")

    if (
        data.get("looks_outdated")
        or (data.get("load_speed_tier") in ("slow", "very_slow"))
        or ((data.get("response_time_ms") or 0) > 3000)
    ):
        score += 10
        reasons.append("Sitio lento o viejo (+10)")

    if data.get("has_phone") or data.get("has_email"):
        score += 8
        reasons.append("Tiene teléfono o email visible (+8)")

    if (data.get("social_count") or 0) > 0 or data.get("has_facebook") or data.get("has_instagram"):
        score += 8
        reasons.append("Tiene presencia en redes sociales (+8)")

    if not data.get("meta_description") or (data.get("meta_desc_length") or 0) < 50:
        score += 5
        reasons.append("Sin meta descripción SEO (+5)")

    if data.get("has_contact_form") and not data.get("has_crm_form"):
        score += 7
        reasons.append("Formulario sin CRM — leads sin automatizar (+7)")

    rubro = (data.get("rubro") or "").strip().lower()
    if rubro in HIGH_DEMAND_SECTORS:
        score += 20
        reasons.append("Rubro con alta demanda de atención (+20)")

    score = clamp(score)
    return score, classify(score), reasons
