CMS_FINGERPRINTS = {
    "WordPress": ["/wp-content/", "/wp-includes/", "/wp-json/", "wordpress"],
    "Elementor": ["elementor-widget", "elementor-section", "elementor/assets", "data-elementor"],
    "Divi": ["et_pb_section", "et_pb_row", "et_pb_column", "et-db", "divi"],
    "Joomla": ["/media/system/js/", 'content="joomla"', "com_content"],
    "Wix": ["wixstatic.com", "wix.com"],
    "Squarespace": ["static.squarespace.com", "squarespace"],
    "Webflow": ["webflow.com", "js.webflow.com", "data-wf-page"],
    "PrestaShop": ["prestashop", "/modules/prestashop", "/themes/classic"],
    "OpenCart": ["route=common/home", "catalog/view/theme"],
    "Magento": ["magento_ui", "mage/cookies", "/static/version", "requirejs/require.js"],
    "Shopify": ["cdn.shopify.com", "shopify.theme", "x-shopify", "/cart.js"],
    "Laravel": ["csrf-token", "laravel_session", "/vendor/laravel"],
    "Drupal": ["sites/default/files", "drupal.js", "drupal-settings-json"],
}

ECOMMERCE_FINGERPRINTS = {
    "WooCommerce": ["woocommerce", "wc-ajax", "/cart/", "/checkout/"],
    "Shopify": ["cdn.shopify.com", "shopify.theme", "x-shopify", "/cart.js"],
    "Magento": ["magento_ui", "mage/cookies", "/customer/account/login"],
    "PrestaShop": ["prestashop", "/order", "add-to-cart"],
    "OpenCart": ["route=checkout", "catalog/view/theme"],
    "VTEX": ["vteximg.com.br", "vtex.com", "vtexcommerce"],
}

FRONTEND_FINGERPRINTS = {
    "Next.js": ["_next/", "__next", "next-route-announcer"],
    "React": ["react", "__react", "data-reactroot", "reactdom"],
    "Vue.js": ["__vue__", "vue-app", "data-v-", "nuxtjs", "__nuxt"],
    "Angular": ["ng-version", "ng-app", "_nghost", "angular/core"],
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
    "WhatsApp Business": ["wa-button", "whatsapp-button", "btn-whatsapp"],
    "Meta Messenger": ["connect.facebook.net/en_US/sdk", "fb-messengermessages"],
    "JivoChat": ["jivosite.com", "jivochat"],
}

WHATSAPP_PATTERNS = [
    "wa.me",
    "api.whatsapp.com",
    "whatsapp://",
    "whatsapp.com/send",
    "btn-whatsapp",
    "whatsapp-float",
    "whatsapp-widget",
]

CONTACT_KEYWORDS = [
    "contacto",
    "contact",
    "contáctanos",
    "escríbenos",
    "ubícanos",
    "donde estamos",
    "visítanos",
    "localización",
    "ubicacion",
    "contact-us",
    "get-in-touch",
    "reach-us",
]

CTA_KEYWORDS = [
    "comprar",
    "cotizar",
    "reservar",
    "agendar",
    "llámanos",
    "escríbenos",
    "contáctanos",
    "solicitar",
    "pedir cita",
    "ver precio",
    "ver precios",
    "consultar",
    "enviar mensaje",
    "más información",
    "ordena ahora",
    "pedir ahora",
    "llamar ahora",
    "envíanos",
    "conoce más",
    "empieza",
    "comenzar",
    "get started",
    "buy now",
    "order now",
    "book now",
]

ECOMMERCE_HINTS = [
    "producto",
    "productos",
    "cart",
    "carrito",
    "checkout",
    "shop",
    "agregar al carrito",
    "añadir al carrito",
    "add to cart",
    "precio",
    "oferta",
    "descuento",
    "envío gratis",
]

CRM_FORM_FINGERPRINTS = {
    "HubSpot Forms": ["hs-script.com", "hsforms.net", "hubspotforms", "js.hsforms.net"],
    "Typeform": ["typeform.com"],
    "Google Forms": ["docs.google.com/forms"],
    "Gravity Forms": ["gravityforms", "gform_wrapper"],
    "Mailchimp": ["list-manage.com", "mailchimp.com/subscribe"],
    "Pipedrive": ["pipedriveleads.com"],
    "ActiveCampaign": ["activehosted.com"],
    "Zoho Forms": ["zohopublic.com", "zohoforms"],
    "Salesforce": ["salesforce.com/servlet", "web-to-lead"],
}

SOCIAL_PATTERNS = {
    "tiktok": ["tiktok.com"],
    "youtube": ["youtube.com", "youtu.be"],
    "linkedin": ["linkedin.com"],
    "twitter": ["twitter.com", "x.com/"],
}

# Parked/empty domain signatures — used in detector to flag useless pages
PARKED_PATTERNS = [
    "domain for sale",
    "buy this domain",
    "this domain is for sale",
    "parked free",
    "sedoparking",
    "dominio en venta",
    "domain parking",
    "this domain has been registered",
    "this web page is parked",
    "godaddy.com/domains",
    "namecheap.com/domains",
    "registro de dominio",
    "hubiese caducado",
    "this domain expired",
    "domain has expired",
    "the domain is registered",
    "domain registrar",
]
