CMS_FINGERPRINTS = {
    "WordPress": ["/wp-content/", "/wp-includes/", "/wp-json/", "wordpress"],
    "Joomla": ["/media/system/js/", 'content="joomla"', "com_content"],
    "Wix": ["wixstatic.com", "wix.com"],
    "Squarespace": ["static.squarespace.com", "squarespace"],
    "PrestaShop": ["prestashop", "/modules/", "/themes/"],
    "OpenCart": ["route=common/home", "catalog/view/theme"],
    "Magento": ["magento_ui", "mage/cookies", "/static/version", "/customer/account/login"],
    "Shopify": ["cdn.shopify.com", "shopify.theme", "x-shopify", "/cart.js"],
    "Laravel": ["csrf-token", "laravel_session", "/vendor/laravel"],
}

ECOMMERCE_FINGERPRINTS = {
    "WooCommerce": ["woocommerce", "wc-ajax", "/cart/", "/checkout/"],
    "Shopify": ["cdn.shopify.com", "shopify.theme", "x-shopify", "/cart.js"],
    "Magento": ["magento_ui", "mage/cookies", "/customer/account/login"],
    "PrestaShop": ["prestashop", "/modules/", "/themes/"],
    "OpenCart": ["route=checkout", "catalog/view/theme"],
}

FRONTEND_FINGERPRINTS = {
    "React": ["react", "__react", "data-reactroot"],
    "Next.js": ["_next/", "__next", "next-route-announcer"],
}

CHATBOT_FINGERPRINTS = {
    "Tawk.to": ["tawk.to"],
    "Crisp": ["crisp.chat"],
    "Intercom": ["intercom"],
    "Zendesk Chat": ["zopim", "zendesk"],
    "Drift": ["drift.com"],
    "HubSpot chat": ["js.hs-scripts.com", "hubspot"],
    "LiveChat": ["livechatinc.com"],
    "ManyChat": ["manychat"],
    "ChatBot.com": ["chatbot.com"],
    "Botpress": ["botpress"],
}

WHATSAPP_PATTERNS = ["wa.me", "api.whatsapp.com", "whatsapp://", "+507"]
CONTACT_KEYWORDS = ["contacto", "contact", "contáctanos", "escríbenos"]
CTA_KEYWORDS = ["comprar", "cotizar", "reservar", "agendar", "llámanos", "escríbenos", "contáctanos"]
ECOMMERCE_HINTS = ["producto", "productos", "cart", "carrito", "checkout", "shop"]
