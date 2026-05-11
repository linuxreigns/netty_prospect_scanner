from .providers import BaseDiscoveryProvider, DiscoveryResult, LocalCatalogProvider, NullWebProvider


class DiscoveryService:
    def __init__(self, providers: list[BaseDiscoveryProvider] | None = None):
        self.providers = providers or [LocalCatalogProvider(), NullWebProvider()]

    def search(self, rubro: str | None = None, provincia: str | None = None, limit: int = 50) -> list[DiscoveryResult]:
        merged: list[DiscoveryResult] = []
        seen = set()
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
