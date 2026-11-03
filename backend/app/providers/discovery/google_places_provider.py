"""Official Google Maps Platform / Places API Discovery Provider."""

from typing import Dict, Any, List, Optional
import httpx
import re
import logging

from app.core.config import settings
from app.providers.discovery.base import BaseDiscoveryProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class GooglePlacesProvider(BaseDiscoveryProvider):
    """
    Official Google Maps Platform / Places API provider for direct local business discovery.
    Uses Google Places Text Search and Place Details APIs.
    """

    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY or settings.GOOGLE_MAPS_API_KEY
        self.timeout = settings.GOOGLE_PLACES_REQUEST_TIMEOUT
        self.text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    def is_configured(self) -> bool:
        """Check if Google Places API key is configured."""
        return bool(self.api_key)

    def get_name(self) -> str:
        """Get provider name."""
        return "google_places"

    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Discover local businesses directly from Google Maps Platform / Places API.
        """
        if not self.is_configured():
            logger.info("[GooglePlacesProvider] API key is not configured in .env.")
            raise ValueError("Google Places API key (GOOGLE_PLACES_API_KEY) is not configured in .env")

        search_query = f"{query} in {location}" if location else query
        params = {
            "query": search_query,
            "key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(self.text_search_url, params=params)
                res.raise_for_status()
                data = res.json()

                status = data.get("status")
                if status in ["REQUEST_DENIED", "OVER_QUERY_LIMIT"]:
                    ProviderHealthService.record_failure("google_places", f"Google Places API {status}: {data.get('error_message')}", IntegrationStatus.INVALID_CREDENTIALS)
                    raise ValueError(f"Google Places API Error: {status} - {data.get('error_message')}")

                results = data.get("results", [])
                businesses = []

                # Limit to requested count
                for raw in results[:limit]:
                    place_id = raw.get("place_id")
                    phone = None
                    website = None

                    # If place_id exists, fetch Place Details for verified phone and website
                    if place_id:
                        try:
                            det_params = {
                                "place_id": place_id,
                                "fields": "formatted_phone_number,international_phone_number,website",
                                "key": self.api_key,
                            }
                            det_res = await client.get(self.place_details_url, params=det_params)
                            if det_res.status_code == 200:
                                det_data = det_res.json().get("result", {})
                                phone = det_data.get("formatted_phone_number") or det_data.get("international_phone_number")
                                website = det_data.get("website")
                        except Exception as e:
                            logger.warning(f"Could not fetch place details for {place_id}: {e}")

                    norm = self.normalize_business(raw, default_location=location, phone=phone, website=website)
                    businesses.append(norm)

                ProviderHealthService.record_success("google_places")
                return {
                    "businesses": businesses,
                    "provider_job_id": f"places_{search_query.replace(' ', '_')[:30]}",
                    "total_found": len(businesses),
                }

        except Exception as e:
            logger.error(f"Google Places discovery error: {e}")
            ProviderHealthService.record_failure("google_places", str(e))
            raise

    def normalize_business(
        self,
        raw_data: Dict[str, Any],
        default_location: str = "",
        phone: Optional[str] = None,
        website: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalize Google Places API result into standard business lead schema.
        """
        raw_address = raw_data.get("formatted_address") or ""
        city, state, country = self._parse_location(raw_address, default_location)

        rating = raw_data.get("rating")
        reviews = raw_data.get("user_ratings_total")
        desc_parts = []
        if rating:
            desc_parts.append(f"Google Rating: {rating} ({reviews or 0} reviews)")
        if raw_data.get("business_status"):
            desc_parts.append(str(raw_data.get("business_status")).replace("_", " ").title())
        
        types = raw_data.get("types", [])
        primary_category = types[0].replace("_", " ").title() if types else "Local Business"

        return {
            "business_name": raw_data.get("name") or "Unknown Business",
            "category": primary_category,
            "description": " • ".join(desc_parts) if desc_parts else None,
            "address": raw_address or None,
            "city": city,
            "state": state,
            "country": country,
            "website": website,
            "phone": phone,
            "source_provider": "google_places",
            "provider_external_id": raw_data.get("place_id"),
        }

    def _parse_location(self, address: str, default_location: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse city, state, country from formatted address."""
        city = None
        state = None
        country = None

        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 3:
                country = parts[-1]
                state_zip = parts[-2]
                state = re.sub(r'\d+', '', state_zip).strip() or state_zip
                city = parts[-3]
            elif len(parts) == 2:
                city = parts[0]
                country = parts[1]
            elif len(parts) == 1:
                city = parts[0]

        if not city and default_location:
            loc_parts = [p.strip() for p in default_location.split(",") if p.strip()]
            city = loc_parts[0]
            if len(loc_parts) > 1:
                country = loc_parts[-1]

        return city, state, country
