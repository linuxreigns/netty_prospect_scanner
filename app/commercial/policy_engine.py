from app.models import Prospect

MANAGER_ROLES = {"ops_manager", "sales_manager", "admin"}


def requires_manager_approval(prospect: Prospect, channel: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    score = int(prospect.netty_fit_score or 0)

    if score >= 85:
        reasons.append("Score >= 85")
    if channel == "whatsapp":
        reasons.append("Canal WhatsApp requiere control adicional")
    if (prospect.rubro or "").strip().lower() in {"clinicas", "abogados", "aseguradoras"}:
        reasons.append("Rubro sensible")

    return (len(reasons) > 0, reasons)


def is_manager(actor: str | None) -> bool:
    return (actor or "").strip().lower() in MANAGER_ROLES
