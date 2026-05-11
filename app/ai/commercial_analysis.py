import json

import httpx

from app.config import settings

from .prompts import build_commercial_prompt


def _default_base_url(provider: str) -> str:
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com/v1"
    return ""


def analyze_commercial_fit(prospect: dict) -> dict:
    """IA opcional para análisis comercial (NO scraping técnico)."""
    provider = (settings.ai_provider or "none").lower()
    api_key = settings.ai_api_key
    model = settings.ai_model or ("gpt-4o-mini" if provider == "openai" else "deepseek-chat")
    prompt = build_commercial_prompt(prospect)

    if provider not in {"openai", "deepseek"} or not api_key:
        return {
            "enabled": False,
            "message": "Proveedor IA no configurado. Defina AI_PROVIDER y AI_API_KEY.",
            "prompt_preview": prompt,
        }

    base_url = settings.ai_base_url or _default_base_url(provider)
    if not base_url.startswith("https://"):
        return {
            "enabled": False,
            "provider": provider,
            "model": model,
            "error": "AI_BASE_URL inseguro: solo se permite HTTPS.",
        }

    url = f"{base_url.rstrip('/')}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Eres un asesor comercial B2B experto en ventas consultivas y automatización con chatbots.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=40) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return {
            "enabled": True,
            "provider": provider,
            "model": model,
            "analysis_text": content,
            "raw": data,
        }
    except Exception as exc:
        return {
            "enabled": False,
            "provider": provider,
            "model": model,
            "error": str(exc),
            "request_preview": json.dumps(payload, ensure_ascii=False)[:3000],
        }
