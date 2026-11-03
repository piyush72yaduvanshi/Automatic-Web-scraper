"""Apify Google Maps business discovery provider."""

import asyncio
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.providers.discovery.base import BaseDiscoveryProvider


class ApifyMapsProvider(BaseDiscoveryProvider):
    """
    Apify Google Maps Scraper provider for business discovery.
    
    Uses official Apify API to discover businesses from Google Maps.
    """
    
    def __init__(self):
        self.api_token = settings.APIFY_API_TOKEN
        self.actor_id = settings.APIFY_MAPS_ACTOR_ID
        self.timeout = settings.APIFY_REQUEST_TIMEOUT
        self.base_url = "https://api.apify.com/v2"
    
    def is_configured(self) -> bool:
        """Check if Apify API token is configured."""
        return bool(self.api_token)
    
    def get_name(self) -> str:
        """Get provider name."""
        return "apify"
    
    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Discover businesses using Apify Google Maps Scraper.
        
        Args:
            query: Business category or keyword
            location: City, state, country
            radius_km: Search radius in kilometers (not used by this actor)
            limit: Maximum number of results
            
        Returns:
            Dictionary with businesses, provider_job_id, and total_found
        """
        if not self.is_configured():
            raise ValueError("Apify API token not configured")
        
        # Construct search query
        search_query = f"{query} in {location}"
        
        # Prepare actor input
        # Based on Apify Google Maps Scraper documentation
        actor_input = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": limit,
            "language": "en",
            "includeWebsite": True,
            "includeOpeningHours": False,
            "includeReviews": False,
            "includePeopleAlsoSearch": False,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Start actor run
            run_response = await client.post(
                f"{self.base_url}/acts/{self.actor_id}/runs",
                params={"token": self.api_token},
                json=actor_input,
            )
            run_response.raise_for_status()
            run_data = run_response.json()
            
            run_id = run_data["data"]["id"]
            
            # Wait for completion
            await self._wait_for_completion(client, run_id)
            
            # Get results
            dataset_id = run_data["data"]["defaultDatasetId"]
            results = await self._get_dataset_items(client, dataset_id)
            
            # Normalize results
            businesses = [self.normalize_business(item) for item in results]
            
            return {
                "businesses": businesses,
                "provider_job_id": run_id,
                "total_found": len(businesses),
            }
    
    async def _wait_for_completion(self, client: httpx.AsyncClient, run_id: str, max_wait: int = 300):
        """
        Wait for actor run to complete.
        
        Args:
            client: HTTP client
            run_id: Actor run ID
            max_wait: Maximum wait time in seconds
        """
        elapsed = 0
        poll_interval = 5
        
        while elapsed < max_wait:
            response = await client.get(
                f"{self.base_url}/actor-runs/{run_id}",
                params={"token": self.api_token},
            )
            response.raise_for_status()
            run_info = response.json()
            
            status = run_info["data"]["status"]
            
            if status == "SUCCEEDED":
                return
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Actor run {status}: {run_info.get('data', {}).get('statusMessage', '')}")
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"Actor run did not complete within {max_wait} seconds")
    
    async def _get_dataset_items(self, client: httpx.AsyncClient, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Get items from Apify dataset.
        
        Args:
            client: HTTP client
            dataset_id: Dataset ID
            
        Returns:
            List of dataset items
        """
        response = await client.get(
            f"{self.base_url}/datasets/{dataset_id}/items",
            params={"token": self.api_token, "format": "json"},
        )
        response.raise_for_status()
        return response.json()
    
    def normalize_business(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Apify Google Maps data to common schema.
        
        Args:
            raw_data: Raw business data from Apify
            
        Returns:
            Normalized business dictionary
        """
        # Extract location components
        location = raw_data.get("location", {})
        
        # Handle address field - can be string or dict
        address_field = raw_data.get("address")
        if isinstance(address_field, dict):
            # Address is a dict with components
            address_obj = address_field
            address = address_obj.get("full") or address_obj.get("formatted")
        else:
            # Address is a string or None
            address_obj = {}
            address = address_field if isinstance(address_field, str) else None
        
        # Determine city, state, country from available data
        city = address_obj.get("city") or raw_data.get("city")
        state = address_obj.get("state") or raw_data.get("state")
        country = address_obj.get("country") or raw_data.get("country")
        
        return {
            "business_name": raw_data.get("title") or raw_data.get("name", "Unknown Business"),
            "category": raw_data.get("categoryName") or raw_data.get("categories", [None])[0],
            "description": raw_data.get("description"),
            "address": address,
            "city": city,
            "state": state,
            "country": country,
            "website": raw_data.get("website") or raw_data.get("url"),
            "source_provider": "apify",
            "provider_external_id": raw_data.get("placeId") or raw_data.get("cid"),
        }
