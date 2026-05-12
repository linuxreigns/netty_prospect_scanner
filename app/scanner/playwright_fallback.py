from typing import Any

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def fetch_rendered_html(url: str, timeout_ms: int = 15000) -> dict[str, Any]:
    """JS-rendered fallback via Playwright (sync, intended for asyncio.to_thread)."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"ok": False, "error": f"Playwright no disponible: {exc}"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                locale="es-PA",
                user_agent=_UA,
            )
            page = context.new_page()

            response = None
            try:
                # networkidle waits until no network activity for 500ms
                response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            except Exception:
                # Long-polling / websocket sites never reach networkidle; fall back
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    page.wait_for_timeout(2500)
                except Exception as exc2:
                    browser.close()
                    return {"ok": False, "error": str(exc2)}

            # Scroll to trigger lazy-loaded content
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(600)
            except Exception:
                pass

            html = page.content()
            final_url = page.url
            status = response.status if response else None
            browser.close()
            return {"ok": True, "html": html, "status": status, "url": final_url}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
