import os
import logging
import requests
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)

class GoogleMapsClient:
    """Google Maps Geocoding API client for address to coordinates conversion"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests to avoid rate limiting

    def _make_request(self, address: str) -> Optional[dict]:
        """Make a geocoding request with rate limiting"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)

            params = {
                'address': address,
                'key': self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            self.last_request_time = time.time()

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Google Maps API request failed for address '{address}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during geocoding for address '{address}': {e}")
            return None

    def geocode_address(self, address: str) -> Optional[Tuple[str, str]]:
        """
        Convert address to coordinates (latitude, longitude)

        Args:
            address: The address to geocode

        Returns:
            Tuple of (latitude, longitude) as strings, or None if geocoding fails
        """
        if not address or not address.strip():
            logger.warning("Empty address provided for geocoding")
            return None

        try:
            logger.info(f"Geocoding address: {address}")

            # Import here to avoid circular imports in some contexts
            try:
                from services.address_simplifier import AddressSimplifier
            except Exception:
                # fallback import path used in tests/run-from-root scenarios
                from email_processor.src.services.address_simplifier import AddressSimplifier  # type: ignore

            simplified = AddressSimplifier.simplify_address(address)
            logger.info(f"Simplified address for geocoding: '{simplified}' (original: '{address}')")

            # First try with simplified address
            data = self._make_request(simplified)
            if not data:
                return None

            if data.get('status') != 'OK':
                logger.warning(f"Geocoding failed for address '{simplified}': {data.get('status')} - {data.get('error_message', 'No error message')}")
                # If simplified failed, try original as last resort
                data = self._make_request(address)
                if not data or data.get('status') != 'OK':
                    return None

            results = data.get('results', [])
            if not results:
                logger.warning(f"No results found for address: {simplified}")
                return None

            top = results[0]
            formatted = top.get('formatted_address', '')

            # Enforce strict matching: only accept results that appear to be an exact/close match
            if not AddressSimplifier.is_strict_match(simplified, formatted):
                logger.warning(f"Geocoding result '{formatted}' does not strictly match simplified address '{simplified}'. Rejecting.")
                # Do not accept lower-precision matches (e.g., city-only)
                return None

            location = top.get('geometry', {}).get('location', {})
            lat = location.get('lat')
            lng = location.get('lng')

            if lat is None or lng is None:
                logger.warning(f"Invalid coordinates received for address: {simplified}")
                return None

            logger.info(f"Successfully geocoded address '{simplified}' to ({lat}, {lng})")
            return (str(lat), str(lng))

        except Exception as e:
            logger.error(f"Error during geocoding for address '{address}': {e}")
            return None

    def close(self):
        """Close the client (placeholder for consistency with other clients)"""
        pass

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()