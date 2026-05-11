from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(_header)) -> None:
    """Valida X-API-Key. Si API_KEY no está configurada, permite todo (modo dev)."""
    if not settings.api_key:
        return
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key inválida o ausente",
        )
