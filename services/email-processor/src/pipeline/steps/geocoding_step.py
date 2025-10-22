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

    def _geocode_single_address(self, original_address: str) -> Optional[str]:
        """
        Attempts to geocode an address, first with the original string,
        and then with a simplified version if the first attempt is not precise.
        Returns formatted coordinates string or None.
        """
        if not original_address:
            return None

        # Attempt 1: Geocode the original address
        self.logger.info(f"Attempting to geocode original address: {original_address}")
        geo_result = self.google_maps_client.geocode_address(original_address)

        # Check for a high-quality result
        if geo_result:
            location = geo_result.get('geometry', {}).get('location', {})
            location_type = geo_result.get('geometry', {}).get('location_type')
            partial_match = geo_result.get('partial_match', False)

            if location_type == 'ROOFTOP' and not partial_match:
                self.logger.info(f"Got high-confidence 'ROOFTOP' match for original address.")
                lat, lng = location.get('lat'), location.get('lng')
                return f"{lat}, {lng}"

            self.logger.warning(f"Original geocode result was not precise (type: {location_type}, partial: {partial_match}).")

        # Attempt 2: Simplify the address and retry
        simplified_address = AddressSimplifier.simplify_address(original_address)
        self.logger.info(f"Retrying with simplified address: {simplified_address}")
        geo_result_simplified = self.google_maps_client.geocode_address(simplified_address)

        if geo_result_simplified:
            # Final validation using is_strict_match
            formatted_address = geo_result_simplified.get('formatted_address', '')
            if AddressSimplifier.is_strict_match(simplified_address, formatted_address):
                location = geo_result_simplified.get('geometry', {}).get('location', {})
                lat, lng = location.get('lat'), location.get('lng')
                self.logger.info(f"Successfully geocoded simplified address with strict match.")
                return f"{lat}, {lng}"
            else:
                self.logger.error(f"Geocoding of simplified address FAILED strict match validation.")

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
                coords = self._geocode_single_address(context.logistics_data.loading_address)
                if coords:
                    context.logistics_data.loading_coordinates = coords
                    coordinates_filled += 1
                else:
                    self.logger.error(f"All geocoding attempts failed for loading address: {context.logistics_data.loading_address}")

            if not context.logistics_data.unloading_coordinates and context.logistics_data.unloading_address:
                coords = self._geocode_single_address(context.logistics_data.unloading_address)
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