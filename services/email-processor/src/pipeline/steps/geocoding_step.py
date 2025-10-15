from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from clients.google_maps_client import GoogleMapsClient
from pipeline.processing_context import ProcessingContext


class GeocodingStep(ProcessingStep):
    """Step for filling missing coordinates using Google Maps Geocoding API"""

    def __init__(self, google_maps_client: GoogleMapsClient):
        super().__init__(ProcessingOrder.GEOCODING)
        self.google_maps_client = google_maps_client

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Fill missing coordinates in the logistics data using Google Maps API

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

            # Fill loading coordinates if missing
            if not context.logistics_data.loading_coordinates and context.logistics_data.loading_address:
                self.logger.info(f"Attempting to geocode loading address: {context.logistics_data.loading_address}")
                coords = self.google_maps_client.geocode_address(context.logistics_data.loading_address)
                if coords:
                    context.logistics_data.loading_coordinates = f"{coords[0]}, {coords[1]}"
                    coordinates_filled += 1
                    self.logger.info(f"Successfully geocoded loading address to: {context.logistics_data.loading_coordinates}")
                else:
                    self.logger.warning(f"Failed to geocode loading address: {context.logistics_data.loading_address}")

            # Fill unloading coordinates if missing
            if not context.logistics_data.unloading_coordinates and context.logistics_data.unloading_address:
                self.logger.info(f"Attempting to geocode unloading address: {context.logistics_data.unloading_address}")
                coords = self.google_maps_client.geocode_address(context.logistics_data.unloading_address)
                if coords:
                    context.logistics_data.unloading_coordinates = f"{coords[0]}, {coords[1]}"
                    coordinates_filled += 1
                    self.logger.info(f"Successfully geocoded unloading address to: {context.logistics_data.unloading_coordinates}")
                else:
                    self.logger.warning(f"Failed to geocode unloading address: {context.logistics_data.unloading_address}")

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