from app.scanner.detector import detect_signals, detect_technology


def test_detect_wordpress_and_woocommerce():
    html = """
    <html><head><meta name='generator' content='WordPress'></head>
    <body>
      <script src='/wp-content/themes/x.js'></script>
      <a href='/cart/'>Carrito</a>
      <a href='/checkout/'>Checkout</a>
      <a href='https://wa.me/50760001111'>WhatsApp</a>
      <form action='/contact'></form>
    </body></html>
    """
    tech = detect_technology(html, headers={"x-powered-by": "PHP/8.2"})
    sig = detect_signals("https://example.com", html)

    assert tech["cms"] == "WordPress"
    assert tech["ecommerce_platform"] == "WooCommerce"
    assert sig["has_whatsapp"] is True
    assert sig["has_contact_form"] is True


def test_detect_chatbot_vendor():
    html = "<script src='https://embed.tawk.to/abc/default'></script>"
    sig = detect_signals("https://example.com", html)
    assert sig["has_chatbot"] is True
    assert sig["chatbot_vendor"] == "Tawk.to"


def test_detect_elementor_and_divi():
    html_elementor = "<div class='elementor-section'><div class='elementor-widget'>content</div></div>"
    html_divi = "<div class='et_pb_section'><div class='et_pb_row'>content</div></div>"
    assert detect_technology(html_elementor, {})["cms"] == "Elementor"
    assert detect_technology(html_divi, {})["cms"] == "Divi"


def test_extract_phone_from_tel_link():
    html = "<a href='tel:+50766001234'>Llámanos</a>"
    sig = detect_signals("https://example.com", html)
    assert sig["has_phone"] is True
    assert "66001234" in (sig["phone_numbers"] or "")


def test_extract_email_from_mailto_link():
    html = "<a href='mailto:ventas@empresa.com.pa'>Escríbenos</a>"
    sig = detect_signals("https://example.com", html)
    assert sig["has_email"] is True
    assert "ventas@empresa.com.pa" in (sig["email_addresses"] or "")


def test_detect_parked_domain():
    html = "<html><head><title>Domain for Sale</title></head><body>Buy this domain at godaddy.com</body></html>"
    sig = detect_signals("https://example.com", html)
    assert sig["is_parked"] is True


def test_normal_site_not_parked():
    html = """<html><head><title>Restaurante El Rancho</title></head>
    <body><h1>Bienvenidos</h1><p>Somos un restaurante en Panamá</p></body></html>"""
    sig = detect_signals("https://elrancho.com.pa", html)
    assert sig["is_parked"] is False


def test_extract_whatsapp_number():
    html = "<a href='https://wa.me/50766001234'>WhatsApp</a>"
    sig = detect_signals("https://example.com", html)
    assert sig["has_whatsapp"] is True
    assert sig["whatsapp_number"] == "+50766001234"


def test_detect_vue_frontend():
    html = "<div id='app' data-v-abc123><script>window.__vue__ = true</script></div>"
    tech = detect_technology(html, {})
    assert tech["frontend_stack"] == "Vue.js"


def test_schema_org_extraction():
    html = """<html><head>
    <script type="application/ld+json">
    {"@type":"LocalBusiness","name":"Restaurante El Ranchito","telephone":"+507 6000-1234",
     "email":"info@elranchito.com","address":{"streetAddress":"Calle 50, Local 3","addressLocality":"Panamá"},
     "openingHours":"Mo-Fr 08:00-18:00","priceRange":"$$"}
    </script></head><body><h1>El Ranchito</h1></body></html>"""
    sig = detect_signals("https://elranchito.com", html)
    assert "+507 6000-1234" in (sig["phone_numbers"] or "")
    assert "info@elranchito.com" in (sig["email_addresses"] or "")
    assert "Calle 50" in (sig["address"] or "")
    assert sig["schema_hours"] is not None
    assert sig["schema_price_range"] == "$$"
    assert sig["has_schema_markup"] is True


def test_vendor_email_filtered():
    html = """<html><body>
    <a href="mailto:ventas@empresa.com">Ventas</a>
    <script>var x = 'support@starapps.studio'</script>
    </body></html>"""
    sig = detect_signals("https://empresa.com", html)
    assert "ventas@empresa.com" in (sig["email_addresses"] or "")
    assert "starapps.studio" not in (sig["email_addresses"] or "")


def test_tiktok_url_extracted():
    html = "<a href='https://www.tiktok.com/@mitienda'>TikTok</a>"
    sig = detect_signals("https://mitienda.com", html)
    assert sig.get("tiktok_url") == "https://www.tiktok.com/@mitienda"
    assert sig["has_tiktok"] is True


def test_phone_max_11_digits():
    # 13-digit barcode-like number should NOT be captured
    html = "<p>SKU: 2940000713242 — Llama al 6000-1234</p>"
    sig = detect_signals("https://tienda.com", html)
    assert "2940000713242" not in (sig["phone_numbers"] or "")


def test_business_name_from_schema():
    html = """<html><head>
    <script type="application/ld+json">
    {"@type":"Store","name":"Tienda Central"}
    </script></head><body></body></html>"""
    sig = detect_signals("https://tiendacentral.com", html)
    assert sig["business_name"] == "Tienda Central"
