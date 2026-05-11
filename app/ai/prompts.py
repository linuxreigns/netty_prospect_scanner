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
