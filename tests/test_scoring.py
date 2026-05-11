from app.scoring.score_engine import compute_score


def test_score_caliente_without_chatbot_and_ecommerce():
    data = {
        "load_ok": True,
        "has_chatbot": False,
        "has_whatsapp": True,
        "has_contact_form": True,
        "ecommerce_platform": "WooCommerce",
        "cms": "WordPress",
        "has_products_or_cart": True,
        "looks_outdated": False,
        "response_time_ms": 1200,
        "has_phone": True,
        "has_email": True,
        "has_facebook": True,
        "has_instagram": False,
        "rubro": "restaurantes",
    }
    score, classification, reasons = compute_score(data)
    assert score >= 80
    assert classification in {"Caliente", "Bueno"}
    assert any("No tiene chatbot" in r for r in reasons)


def test_score_inaccessible_site_capped():
    data = {"load_ok": False}
    score, classification, reasons = compute_score(data)
    assert score <= 20
    assert classification == "Bajo"
    assert any("inaccesible" in r.lower() for r in reasons)
