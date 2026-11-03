"""Base interface for business discovery providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseDiscoveryProvider(ABC):
    """Abstract base class for business discovery providers."""
    
    @abstractmethod
    async def discover_businesses(
        self,
        query: str,
        location: str,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Discover businesses matching the search criteria.
        
        Args:
            query: Business category or keyword
            location: City, state, country
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            Dictionary containing:
                - businesses: List of normalized business dictionaries
                - provider_job_id: Provider's job/run ID for tracking
                - total_found: Total number of businesses found
        """
        pass
    
    @abstractmethod
    def normalize_business(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize provider-specific business data to common schema.
        
        Args:
            raw_data: Raw business data from provider
            
        Returns:
            Normalized business dictionary
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if provider is properly configured with API credentials.
        
        Returns:
            True if configured, False otherwise
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get provider name.
        
        Returns:
            Provider name
        """
        pass
