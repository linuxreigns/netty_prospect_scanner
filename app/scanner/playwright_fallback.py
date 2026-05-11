from typing import Any


def fetch_rendered_html(url: str, timeout_ms: int = 15000) -> dict[str, Any]:
    """Fallback opcional con Playwright. Si Playwright no está disponible, retorna error controlado."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"ok": False, "error": f"Playwright no disponible: {exc}"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            html = page.content()
            final_url = page.url
            status = response.status if response else None
            browser.close()
            return {"ok": True, "html": html, "status": status, "url": final_url}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
