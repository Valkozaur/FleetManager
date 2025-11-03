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

    def geocode_address(self, address: str) -> Optional[dict]:
        """
        Convert address to coordinates (latitude, longitude)

        Args:
            address: The address to geocode

        Returns:
            The entire first result object from the Google Maps API, or None if geocoding fails
        """
        if not address or not address.strip():
            logger.warning("Empty address provided for geocoding")
            return None

        try:
            logger.info(f"Geocoding address: {address}")

            data = self._make_request(address)
            if not data:
                return None

            if data.get('status') != 'OK':
                logger.warning(f"Geocoding failed for address '{address}': {data.get('status')} - {data.get('error_message', 'No error message')}")
                return None

            results = data.get('results', [])
            if not results:
                logger.warning(f"No results found for address: {address}")
                return None

            # Return the entire first result for detailed analysis
            return results[0]

        except Exception as e:
            logger.error(f"Error during geocoding for address '{address}': {e}")
            return None

    def close(self):
        """Close the client (placeholder for consistency with other clients)"""
        pass

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()