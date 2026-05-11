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
