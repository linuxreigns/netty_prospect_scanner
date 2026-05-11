import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiscoveryResult:
    url: str
    rubro: str | None = None
    provincia: str | None = None
    source: str = "local_catalog"


class BaseDiscoveryProvider:
    name = "base"

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        raise NotImplementedError


class LocalCatalogProvider(BaseDiscoveryProvider):
    name = "local_catalog"

    def __init__(self, csv_path: str = "data/discovery_catalog.csv") -> None:
        self.csv_path = Path(csv_path)

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        if not self.csv_path.exists():
            return []

        out: list[DiscoveryResult] = []
        with self.csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = (row.get("url") or "").strip()
                rr = (row.get("rubro") or "").strip()
                pp = (row.get("provincia") or "").strip()
                if not url:
                    continue
                if rubro and rr.lower() != rubro.lower():
                    continue
                if provincia and pp.lower() != provincia.lower():
                    continue
                out.append(DiscoveryResult(url=url, rubro=rr or None, provincia=pp or None, source=self.name))
                if len(out) >= limit:
                    break
        return out


class NullWebProvider(BaseDiscoveryProvider):
    """Proveedor placeholder para futura integración (Google Maps, directorios, etc.)."""

    name = "web_discovery_placeholder"

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        return []
