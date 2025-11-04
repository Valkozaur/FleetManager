from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from clients.google_maps_client import GoogleMapsClient
from pipeline.processing_context import ProcessingContext
from services.address_simplifier import AddressSimplifier
from typing import Optional


class GeocodingStep(ProcessingStep):
    """Step for filling missing coordinates using Google Maps Geocoding API"""

    def __init__(self, google_maps_client: GoogleMapsClient):
        super().__init__(ProcessingOrder.GEOCODING)
        self.google_maps_client = google_maps_client

    def _geocode_address(self, original_address: str) -> Optional[str]:
        """
        Geocodes an address using a four-tier waterfall strategy.
        Returns formatted coordinates string or None.
        """
        if not original_address:
            return None

        # Geocode original address
        self.logger.info(f"Geocoding original address: {original_address}")
        geocode_result = self.google_maps_client.geocode_address(original_address)

        if geocode_result:
            location = geocode_result.get('geometry', {}).get('location', {})
            location_type = geocode_result.get('geometry', {}).get('location_type')
            partial_match = geocode_result.get('partial_match', False)
            lat, lng = location.get('lat'), location.get('lng')

            # Attempt 1: The "Golden Match"
            if location_type == 'ROOFTOP' and not partial_match:
                self.logger.info("Success with Attempt 1 (Golden Match)")
                return f"{lat}, {lng}"

            # Attempt 2: The "Confirmed Match"
            if location_type == 'ROOFTOP':
                self.logger.info("Success with Attempt 2 (Confirmed ROOFTOP Match)")
                return f"{lat}, {lng}"

        # Attempt 3: The "Validated Simplified Match"
        simplified_address = AddressSimplifier.simplify_address(original_address)
        self.logger.info(f"Attempting geocoding with simplified address: {simplified_address}")
        simplified_result = self.google_maps_client.geocode_address(simplified_address)

        if simplified_result:
            simplified_location_type = simplified_result.get('geometry', {}).get('location_type')
            if simplified_location_type in ['ROOFTOP', 'RANGE_INTERPOLATED']:
                formatted_address = simplified_result.get('formatted_address', '')
                if AddressSimplifier.is_strict_match(simplified_address, formatted_address):
                    location = simplified_result.get('geometry', {}).get('location', {})
                    lat, lng = location.get('lat'), location.get('lng')
                    self.logger.info("Success with Attempt 3 (Validated Simplified Match)")
                    return f"{lat}, {lng}"

        # Attempt 4: The "Best Effort Match"
        if geocode_result and geocode_result.get('geometry', {}).get('location_type') == 'GEOMETRIC_CENTER':
            location = geocode_result.get('geometry', {}).get('location', {})
            lat, lng = location.get('lat'), location.get('lng')
            self.logger.info("Success with Attempt 4 (Best Effort GEOMETRIC_CENTER Match)")
            return f"{lat}, {lng}"

        self.logger.error(f"All geocoding attempts failed for address: {original_address}")
        return None

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Fill missing coordinates in the logistics data using Google Maps API
        Uses cleaned addresses from ADDRESS_CLEANING step if available

        Args:
            context: Processing context containing logistics data with potentially missing coordinates

        Returns:
            ProcessingResult indicating success/failure of geocoding
        """
        if not context.logistics_data:
            return ProcessingResult(
                success=False,
                error="No logistics data available for geocoding"
            )

        try:
            self.logger.info(f"Starting geocoding for logistics data")
            coordinates_filled = 0

            if not context.logistics_data.loading_coordinates and context.logistics_data.loading_address:
                coords = self._geocode_address(context.logistics_data.loading_address)
                if coords:
                    context.logistics_data.loading_coordinates = coords
                    coordinates_filled += 1
                else:
                    self.logger.error(f"All geocoding attempts failed for loading address: {context.logistics_data.loading_address}")

            if not context.logistics_data.unloading_coordinates and context.logistics_data.unloading_address:
                coords = self._geocode_address(context.logistics_data.unloading_address)
                if coords:
                    context.logistics_data.unloading_coordinates = coords
                    coordinates_filled += 1
                else:
                    self.logger.error(f"All geocoding attempts failed for unloading address: {context.logistics_data.unloading_address}")

            self.logger.info(f"Geocoding completed. Filled {coordinates_filled} coordinates.")
            return ProcessingResult(
                success=True,
                data={"coordinates_filled": coordinates_filled}
            )

        except Exception as e:
            error_msg = f"Error during geocoding: {str(e)}"
            self.logger.exception(error_msg)
            return ProcessingResult(
                success=False,
                error=error_msg
            )

    def should_process(self, context: ProcessingContext) -> bool:
        """
        Only process geocoding if we have logistics data with missing coordinates

        Args:
            context: Processing context

        Returns:
            True if geocoding should be attempted
        """
        if not context.has_logistics_data():
            return False

        logistics = context.logistics_data
        return (
            (logistics.loading_address and not logistics.loading_coordinates) or
            (logistics.unloading_address and not logistics.unloading_coordinates)
        )