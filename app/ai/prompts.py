def build_commercial_prompt(prospect: dict) -> str:
    return f"""
Analiza este prospecto B2B y genera:
1) resumen comercial
2) razón por la que puede necesitar Netty
3) mensaje inicial de WhatsApp
4) email frío
5) pitch personalizado
6) objeciones probables
7) recomendación de plan (Starter, Pro o Business)

Datos del prospecto:
{prospect}
""".strip()


def build_proposal_prompt(ctx: dict) -> str:
    opps = "\n".join(f"- {o}" for o in ctx.get("opportunities", [])) or "- Oportunidades de automatización detectadas"
    recs = "\n".join(f"- {r}" for r in ctx.get("recommendations", [])) or "- Automatización con Netty"
    domain = ctx.get("domain", "el sitio")

    return f"""Eres el sistema de IA de NETTY SALES ENGINE.
Acabas de analizar automáticamente el sitio web de un negocio en Panamá y debes generar una propuesta comercial persuasiva.

DATOS DEL PROSPECTO:
- Dominio: {domain}
- Sector/Rubro: {ctx.get("rubro") or "No especificado"}
- Tecnología detectada: CMS={ctx.get("cms") or "desconocido"}, eCommerce={ctx.get("ecommerce") or "ninguno"}
- Score Netty Fit: {ctx.get("score")}/100 — Clasificación: {ctx.get("classification")}
- Tiene chatbot: {"Sí" if ctx.get("has_chatbot") else "No"}
- Tiene WhatsApp: {"Sí" if ctx.get("has_whatsapp") else "No"}
- Tiene eCommerce: {"Sí" if ctx.get("has_ecommerce") else "No"}

OPORTUNIDADES DETECTADAS:
{opps}

RECOMENDACIONES:
{recs}

Genera una propuesta comercial en JSON con exactamente estos campos:
{{
  "audit_summary": "2-3 oraciones describiendo el análisis automático de NETTY SALES ENGINE sobre {domain}, mencionando tecnología detectada y brechas.",
  "value_proposition": "2-3 oraciones sobre cómo Netty resuelve las brechas para este sector específico.",
  "pitch": "1 oración de pitch impactante para este negocio.",
  "plan_recommendation": "Starter|Pro|Business",
  "plan_justification": "1-2 oraciones justificando el plan.",
  "meta_note": "1 oración que refuerza que este análisis fue automático por el ecosistema Netty."
}}

Responde SOLO con el JSON válido, sin texto adicional ni markdown.
""".strip()


def build_outreach_prompt(ctx: dict) -> str:
    opps = ctx.get("opportunities", [])
    top_opp = opps[0] if opps else "oportunidades de automatización detectadas"
    domain = ctx.get("domain", "el sitio")

    return f"""Eres el agente de outreach de NETTY SALES ENGINE.
Acabas de analizar automáticamente {domain} en Panamá.

CONTEXTO:
- Dominio: {domain}
- Sector: {ctx.get("rubro") or "negocio"}
- Score: {ctx.get("score")}/100 ({ctx.get("classification")})
- Principal oportunidad: {top_opp}
- Tecnología: {ctx.get("cms") or "web estándar"}
- Tiene chatbot: {"Sí" if ctx.get("has_chatbot") else "No"}

Genera mensajes de contacto en JSON:
{{
  "whatsapp_draft": "Máximo 3 oraciones: mencionar que el sistema analizó {domain} automáticamente, citar la oportunidad detectada, terminar con pregunta de apertura específica.",
  "email_subject": "Asunto: máximo 60 caracteres.",
  "email_body": "Email 4 párrafos: presentación análisis automático, hallazgos reales, cómo Netty resuelve, CTA. En primera persona de Netty Sales Engine."
}}

Responde SOLO con JSON válido, sin texto adicional ni markdown.
""".strip()
