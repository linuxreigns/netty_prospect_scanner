from app.config import settings

from .providers import BaseDiscoveryProvider, DiscoveryResult, DuckDuckGoProvider, LocalCatalogProvider, NullWebProvider


def _default_providers() -> list[BaseDiscoveryProvider]:
    providers: list[BaseDiscoveryProvider] = [LocalCatalogProvider()]
    if settings.enable_duckduckgo_discovery:
        providers.append(DuckDuckGoProvider(max_results_per_query=settings.duckduckgo_results_per_query))
    else:
        providers.append(NullWebProvider())
    return providers


class DiscoveryService:
    def __init__(self, providers: list[BaseDiscoveryProvider] | None = None):
        self.providers = providers if providers is not None else _default_providers()

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        merged: list[DiscoveryResult] = []
        seen: set[str] = set()
        for provider in self.providers:
            for r in provider.search(rubro=rubro, provincia=provincia, limit=limit):
                key = r.url.lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(r)
                if len(merged) >= limit:
                    return merged
        return merged
