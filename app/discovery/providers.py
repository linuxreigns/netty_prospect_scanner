import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# Dominios a ignorar: redes sociales, directorios, agregadores
_SKIP_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
    "yelp.com",
    "tripadvisor.com",
    "tripadvisor.es",
    "tripadvisor.co",
    "google.com",
    "maps.google.com",
    "goo.gl",
    "bit.ly",
    "wikipedia.org",
    "amazon.com",
    "mercadolibre.com",
    "olx.com",
    "encuentra24.com",
    "wanderlog.com",
    "foursquare.com",
    "zomato.com",
    "happycow.net",
    "infopaginas.com",
    "paginasamarillas.com",
    "paginas-amarillas.com.pa",
}

# Queries que favorecen sitios propios de negocios (no directorios)
_QUERY_TEMPLATES = [
    "{rubro} {provincia} Panamá reservas contacto",
    "{rubro} {provincia} Panamá sitio oficial",
    "{rubro} Panamá WhatsApp +507",
    "{rubro} {provincia} Panamá horario dirección",
]


def _clean_url(raw: str) -> str | None:
    try:
        parsed = urlparse(raw)
        if parsed.scheme not in ("http", "https"):
            return None
        netloc = parsed.netloc.lower()
        domain = netloc[4:] if netloc.startswith("www.") else netloc
        for skip in _SKIP_DOMAINS:
            if domain == skip or domain.endswith("." + skip):
                return None
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None


def _looks_panama(text: str) -> bool:
    text = text.lower()
    signals = ["panamá", "panama", "+507", ".pa", "yappy", "provincia", "507"]
    return any(s in text for s in signals)


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


class DuckDuckGoProvider(BaseDiscoveryProvider):
    """Descubrimiento autónomo via DuckDuckGo — genera queries por rubro/provincia."""

    name = "duckduckgo"

    def __init__(self, max_results_per_query: int = 10) -> None:
        self.max_results_per_query = max_results_per_query

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        try:
            from ddgs import DDGS
        except ImportError:
            log.warning("ddgs no instalado — proveedor DDG deshabilitado")
            return []

        rubro_str = rubro or "negocios"
        prov_str = provincia or "Panamá"
        queries = [t.format(rubro=rubro_str, provincia=prov_str) for t in _QUERY_TEMPLATES]

        seen: set[str] = set()
        out: list[DiscoveryResult] = []

        for query in queries:
            if len(out) >= limit:
                break
            try:
                with DDGS() as ddgs:
                    results = ddgs.text(query, max_results=self.max_results_per_query, region="pa-es")
                    for r in results:
                        url = _clean_url(r.get("href") or "")
                        if not url or url in seen:
                            continue
                        # Con region="pa-es" ya filtramos por Panamá;
                        # verificación adicional en título/body/url
                        combined = r.get("title", "") + " " + r.get("body", "") + " " + url
                        if not _looks_panama(combined):
                            continue
                        seen.add(url)
                        out.append(DiscoveryResult(url=url, rubro=rubro, provincia=prov_str, source=self.name))
                        if len(out) >= limit:
                            break
            except Exception as exc:
                log.warning("DuckDuckGo query '%s' falló: %s", query, exc)
                continue

        log.info("DuckDuckGoProvider encontró %d resultados para rubro=%s", len(out), rubro)
        return out


class NullWebProvider(BaseDiscoveryProvider):
    """Proveedor placeholder para futura integración (Google Maps, directorios, etc.)."""

    name = "web_discovery_placeholder"

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        return []
