"""SerpAPI Google Maps & Local business discovery provider."""

from typing import Dict, Any, List, Optional
import httpx
import re

from app.core.config import settings
from app.providers.discovery.base import BaseDiscoveryProvider


class SerpApiProvider(BaseDiscoveryProvider):
    """
    SerpAPI provider for ultra-fast business discovery via Google Maps.
    """

    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY or settings.SEARCH_API_KEY
        self.timeout = settings.SEARCH_API_TIMEOUT
        self.base_url = "https://serpapi.com/search"

    def is_configured(self) -> bool:
        """Check if SerpAPI key is configured."""
        return bool(self.api_key)

    def get_name(self) -> str:
        """Get provider name."""
        return "serpapi"

    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Discover businesses using SerpAPI Google Maps engine.
        """
        if not self.is_configured():
            raise ValueError("SerpAPI API key is not configured")

        search_query = f"{query} in {location}" if location else query
        
        params = {
            "engine": "google_maps",
            "q": search_query,
            "api_key": self.api_key,
            "type": "search",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            local_results = data.get("local_results", [])
            search_id = data.get("search_metadata", {}).get("id", "serpapi_job")

            # If Google Maps returned nothing, fallback to google engine with local pack
            if not local_results:
                params["engine"] = "google"
                response = await client.get(self.base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    local_results = data.get("local_results", {}).get("places", [])
                    if not local_results:
                        # Fallback to organic local results
                        organic = data.get("organic_results", [])
                        for org in organic[:limit]:
                            local_results.append({
                                "title": org.get("title"),
                                "website": org.get("link"),
                                "address": location,
                                "type": query,
                                "snippet": org.get("snippet"),
                            })

            businesses = [self.normalize_business(item, location) for item in local_results[:limit]]

            return {
                "businesses": businesses,
                "provider_job_id": str(search_id),
                "total_found": len(businesses),
            }

    def normalize_business(self, raw_data: Dict[str, Any], default_location: str = "") -> Dict[str, Any]:
        """
        Normalize SerpAPI data into standard business lead schema.
        """
        raw_address = raw_data.get("address") or ""
        city, state, country = self._parse_location(raw_address, default_location)

        rating = raw_data.get("rating")
        reviews = raw_data.get("reviews")
        description_parts = []
        if rating:
            description_parts.append(f"Rating: {rating} ({reviews or 0} reviews)")
        if raw_data.get("open_state"):
            description_parts.append(str(raw_data.get("open_state")))
        if raw_data.get("snippet"):
            description_parts.append(str(raw_data.get("snippet")))
        
        description = " • ".join(description_parts) if description_parts else None

        # Clean website URL (strip Google tracking redirects if any)
        website = raw_data.get("website")
        if website and "google.com/url?" in website:
            match = re.search(r'url=([^&]+)', website)
            if match:
                from urllib.parse import unquote
                website = unquote(match.group(1))

        return {
            "business_name": raw_data.get("title") or "Unknown Business",
            "category": raw_data.get("type") or (raw_data.get("types", [None])[0] if raw_data.get("types") else None),
            "description": description,
            "address": raw_address or None,
            "city": city,
            "state": state,
            "country": country,
            "website": website,
            "phone": raw_data.get("phone"),  # Direct phone from map snippet!
            "source_provider": "serpapi",
            "provider_external_id": raw_data.get("place_id") or raw_data.get("data_cid") or raw_data.get("data_id"),
        }

    def _parse_location(self, address: str, default_location: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse city, state, country from address or fallback to default location."""
        city = None
        state = None
        country = None

        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 3:
                country = parts[-1]
                state_zip = parts[-2]
                # Extract state name without pin code numbers
                state = re.sub(r'\d+', '', state_zip).strip() or state_zip
                city = parts[-3]
            elif len(parts) == 2:
                state = parts[-1]
                city = parts[-2]
            elif len(parts) == 1:
                city = parts[0]

        if not city and default_location:
            loc_parts = [p.strip() for p in default_location.split(",") if p.strip()]
            city = loc_parts[0] if loc_parts else None
            if len(loc_parts) >= 2:
                country = loc_parts[-1]
            if len(loc_parts) >= 3:
                state = loc_parts[1]

        return city, state, country

