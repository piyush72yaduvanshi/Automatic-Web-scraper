"""Multi-source business discovery orchestrator."""

from typing import Dict, Any, List, Optional
import asyncio
import re

from app.providers.discovery.base import BaseDiscoveryProvider
from app.providers.discovery.serpapi_provider import SerpApiProvider
from app.providers.discovery.apify_provider import ApifyMapsProvider
from app.providers.discovery.google_places_provider import GooglePlacesProvider
from app.providers.discovery.local_maps_provider import LocalMapsScraperProvider


class MultiSourceDiscoveryOrchestrator(BaseDiscoveryProvider):
    """
    Coordinates multi-source discovery across Local Google Maps Scraper,
    Google Places API, SerpAPI, and Apify.
    """

    def __init__(self):
        self.local_maps_provider = LocalMapsScraperProvider()
        self.serpapi_provider = SerpApiProvider()
        self.apify_provider = ApifyMapsProvider()
        self.google_places_provider = GooglePlacesProvider()

    def get_provider(self, name: str) -> Optional[BaseDiscoveryProvider]:
        """Resolve a specific provider instance by identifier or alias."""
        key = (name or "").lower()
        if key in ["local_maps", "local_maps_scraper", "local", "google_maps_kit", "google_map_scraper"]:
            return self.local_maps_provider
        if key in ["google_places", "places"]:
            return self.google_places_provider
        if key in ["serpapi", "serp"]:
            return self.serpapi_provider
        if key in ["apify"]:
            return self.apify_provider
        return None

    def is_configured(self) -> bool:
        """Check if at least one discovery provider is configured."""
        return (
            self.local_maps_provider.is_configured()
            or self.google_places_provider.is_configured()
            or self.serpapi_provider.is_configured()
            or self.apify_provider.is_configured()
        )

    def get_name(self) -> str:
        """Get provider name."""
        return "multi_source"

    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Discover businesses from preferred provider or multi-source hybrid.
        """
        provider_name = (preferred_provider or "local_maps").lower()

        # 1. Local Google Maps Scraper Kit (Zero cost, unlimited, direct Google Maps + website pass)
        if provider_name in ["local_maps", "local_maps_scraper", "local", "google_maps_kit", "google_map_scraper"]:
            if self.local_maps_provider.is_configured():
                return await self.local_maps_provider.discover_businesses(query, location, radius_km, limit)
            elif not (self.google_places_provider.is_configured() or self.serpapi_provider.is_configured() or self.apify_provider.is_configured()):
                # When explicitly requested and only provider available, call to surface actionable error
                return await self.local_maps_provider.discover_businesses(query, location, radius_km, limit)

        # 2. Direct Official Google Places API
        if provider_name in ["google_places", "google_maps", "places"] and self.google_places_provider.is_configured():
            return await self.google_places_provider.discover_businesses(query, location, radius_km, limit)

        # 3. SerpAPI only (fast default)
        if provider_name == "serpapi" and self.serpapi_provider.is_configured():
            return await self.serpapi_provider.discover_businesses(query, location, radius_km, limit)

        # 4. Apify only
        if provider_name == "apify" and self.apify_provider.is_configured():
            return await self.apify_provider.discover_businesses(query, location, radius_km, limit)

        # 5. Multi-source hybrid: Prioritize Local Maps Scraper, then Google Places / SerpAPI, fallback to Apify
        all_businesses: List[Dict[str, Any]] = []
        job_ids = []

        if self.local_maps_provider.is_configured():
            try:
                res = await self.local_maps_provider.discover_businesses(query, location, radius_km, limit)
                all_businesses.extend(res.get("businesses", []))
                job_ids.append(f"local_maps:{res.get('provider_job_id')}")
            except Exception as e:
                print(f"[DiscoveryOrchestrator] Local Maps Scraper discovery error: {e}")

        if not all_businesses and self.google_places_provider.is_configured():
            try:
                res = await self.google_places_provider.discover_businesses(query, location, radius_km, limit)
                all_businesses.extend(res.get("businesses", []))
                job_ids.append(f"google_places:{res.get('provider_job_id')}")
            except Exception as e:
                print(f"[DiscoveryOrchestrator] Google Places discovery error: {e}")

        if not all_businesses and self.serpapi_provider.is_configured():
            try:
                res = await self.serpapi_provider.discover_businesses(query, location, radius_km, limit)
                all_businesses.extend(res.get("businesses", []))
                job_ids.append(f"serpapi:{res.get('provider_job_id')}")
            except Exception as e:
                print(f"[DiscoveryOrchestrator] SerpAPI discovery error: {e}")

        # If others found nothing and Apify is configured, use Apify as fallback
        if not all_businesses and self.apify_provider.is_configured():
            try:
                res = await self.apify_provider.discover_businesses(query, location, radius_km, limit=limit)
                all_businesses.extend(res.get("businesses", []))
                job_ids.append(f"apify:{res.get('provider_job_id')}")
            except Exception as e:
                print(f"[DiscoveryOrchestrator] Apify fallback error: {e}")
                all_businesses.extend(res.get("businesses", []))
                job_ids.append(f"apify:{res.get('provider_job_id')}")
            except Exception as e:
                print(f"[DiscoveryOrchestrator] Fallback Apify error: {e}")

        # Deduplicate businesses by name and location/domain
        unique_businesses = self._deduplicate_businesses(all_businesses)

        return {
            "businesses": unique_businesses[:limit],
            "provider_job_id": ",".join(job_ids) or "multi_source_job",
            "total_found": len(unique_businesses[:limit]),
        }

    def normalize_business(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize is delegated to individual providers."""
        return raw_data

    def _deduplicate_businesses(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate businesses based on clean business name and website/phone."""
        seen_keys = set()
        deduped = []

        for b in businesses:
            name = (b.get("business_name") or "").lower()
            clean_name = re.sub(r'[^a-z0-9]', '', name)
            website = (b.get("website") or "").lower()
            
            # Key based on clean name + domain or city
            key = (clean_name, website or b.get("city", "").lower())
            if clean_name and key not in seen_keys:
                seen_keys.add(key)
                deduped.append(b)

        return deduped

