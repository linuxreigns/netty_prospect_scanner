from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.config import settings


@dataclass
class QueueItem:
    id: str
    channel: str
    prospect_id: int
    domain: str
    payload: dict
    status: str  # pending|approved|rejected|sent
    created_at: str
    approved_at: str | None = None


LOCAL_QUEUE: deque[QueueItem] = deque(maxlen=5000)


def redis_enabled() -> bool:
    return bool(getattr(settings, "redis_url", None))


def enqueue_local(item: QueueItem) -> dict:
    LOCAL_QUEUE.append(item)
    return asdict(item)


def list_local(status: str | None = None, limit: int = 100) -> list[dict]:
    rows = list(LOCAL_QUEUE)[-limit:]
    if status:
        rows = [r for r in rows if r.status == status]
    return [asdict(r) for r in reversed(rows)]


def approve_local(item_id: str, approve: bool) -> dict | None:
    for item in LOCAL_QUEUE:
        if item.id == item_id:
            item.status = "approved" if approve else "rejected"
            item.approved_at = datetime.now(UTC).isoformat()
            return asdict(item)
    return None
