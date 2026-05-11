import json
import logging

import httpx

from app.config import settings

from .prompts import build_commercial_prompt, build_outreach_prompt, build_proposal_prompt

log = logging.getLogger(__name__)


def _default_base_url(provider: str) -> str:
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com/v1"
    return ""


def _is_ai_ready() -> tuple[bool, str, str, str]:
    """Retorna (ready, provider, model, base_url)."""
    provider = (settings.ai_provider or "none").lower()
    if provider not in {"openai", "deepseek"} or not settings.ai_api_key:
        return False, provider, "", ""
    model = settings.ai_model or ("gpt-4o-mini" if provider == "openai" else "deepseek-chat")
    base_url = settings.ai_base_url or _default_base_url(provider)
    if not base_url.startswith("https://"):
        return False, provider, model, base_url
    return True, provider, model, base_url


def _call_ai(prompt: str, system: str = "Eres un asistente comercial experto de Netty Sales Engine.") -> str | None:
    ready, provider, model, base_url = _is_ai_ready()
    if not ready:
        return None
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "temperature": 0.4,
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=40) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log.warning("AI call failed: %s", exc)
        return None


def generate_proposal_with_ai(ctx: dict) -> dict | None:
    """Genera propuesta enriquecida con IA. Retorna None si IA no disponible."""
    prompt = build_proposal_prompt(ctx)
    raw = _call_ai(prompt)
    if raw is None:
        return None
    # Limpia posibles bloques markdown antes de parsear
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        log.warning("AI proposal response no es JSON válido: %s", clean[:200])
        return None


def generate_outreach_with_ai(ctx: dict) -> dict | None:
    """Genera mensajes de outreach con IA. Retorna None si IA no disponible."""
    prompt = build_outreach_prompt(ctx)
    raw = _call_ai(prompt)
    if raw is None:
        return None
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        log.warning("AI outreach response no es JSON válido: %s", clean[:200])
        return None


def analyze_commercial_fit(prospect: dict) -> dict:
    """IA opcional para análisis comercial del endpoint /ai/prospect/{id}/analysis."""
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
        return {"enabled": False, "provider": provider, "model": model, "error": "AI_BASE_URL inseguro: solo HTTPS."}

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Eres un asesor comercial B2B experto en ventas consultivas y chatbots."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=40) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return {"enabled": True, "provider": provider, "model": model, "analysis_text": content, "raw": data}
    except Exception as exc:
        return {
            "enabled": False,
            "provider": provider,
            "model": model,
            "error": str(exc),
            "request_preview": json.dumps(payload, ensure_ascii=False)[:3000],
        }
