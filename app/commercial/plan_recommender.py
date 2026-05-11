def recommend_plan(score: int, has_ecommerce: bool, has_whatsapp: bool, has_chatbot: bool) -> dict:
    reasons: list[str] = []

    if score >= 85:
        plan = "Business"
        reasons.append("Score alto con prioridad de cierre.")
    elif score >= 65:
        plan = "Pro"
        reasons.append("Buen fit comercial y oportunidad clara.")
    else:
        plan = "Starter"
        reasons.append("Requiere adopción gradual con bajo riesgo.")

    if has_ecommerce:
        if plan == "Starter":
            plan = "Pro"
        reasons.append("Tiene eCommerce, requiere mayor cobertura de automatización.")

    if has_whatsapp and not has_chatbot:
        if plan == "Starter":
            plan = "Pro"
        reasons.append("Canal WhatsApp activo sin chatbot: oportunidad inmediata.")

    if has_chatbot and plan == "Business":
        reasons.append("Ya usa chatbot: propuesta de reemplazo/mejora avanzada.")

    return {"recommended_plan": plan, "reasons": reasons}
