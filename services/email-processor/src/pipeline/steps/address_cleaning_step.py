from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from services.address_cleaner import AddressCleanerService
from pipeline.processing_context import ProcessingContext


class AddressCleaningStep(ProcessingStep):
    """Step for cleaning addresses before geocoding using Gemini AI"""

    def __init__(self, address_cleaner: AddressCleanerService):
        super().__init__(ProcessingOrder.ADDRESS_CLEANING)
        self.address_cleaner = address_cleaner

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Clean addresses in logistics data for better geocoding accuracy
        
        Args:
            context: Processing context containing logistics data with addresses
            
        Returns:
            ProcessingResult indicating success/failure of address cleaning
        """
        if not context.logistics_data:
            return ProcessingResult(
                success=False,
                error="No logistics data available for address cleaning"
            )

        try:
            logistics = context.logistics_data
            cleaned_count = 0
            
            # Store original addresses and clean them
            original_loading = logistics.loading_address
            original_unloading = logistics.unloading_address
            
            # Clean loading address
            if original_loading:
                cleaned_loading = self.address_cleaner.clean_address(original_loading)
                # Store cleaned address in custom_data for geocoding step
                context.set_custom_data('cleaned_loading_address', cleaned_loading)
                context.set_custom_data('original_loading_address', original_loading)
                cleaned_count += 1
                self.logger.info(f"Cleaned loading address: '{original_loading}' -> '{cleaned_loading}'")
            
            # Clean unloading address
            if original_unloading:
                cleaned_unloading = self.address_cleaner.clean_address(original_unloading)
                # Store cleaned address in custom_data for geocoding step
                context.set_custom_data('cleaned_unloading_address', cleaned_unloading)
                context.set_custom_data('original_unloading_address', original_unloading)
                cleaned_count += 1
                self.logger.info(f"Cleaned unloading address: '{original_unloading}' -> '{cleaned_unloading}'")
            
            self.logger.info(f"Address cleaning completed. Cleaned {cleaned_count} addresses.")
            return ProcessingResult(
                success=True,
                data={"addresses_cleaned": cleaned_count}
            )

        except Exception as e:
            error_msg = f"Error during address cleaning: {str(e)}"
            self.logger.exception(error_msg)
            return ProcessingResult(
                success=False,
                error=error_msg
            )

    def should_process(self, context: ProcessingContext) -> bool:
        """
        Only process if we have logistics data with addresses
        
        Args:
            context: Processing context
            
        Returns:
            True if address cleaning should be attempted
        """
        if not context.has_logistics_data():
            return False
        
        logistics = context.logistics_data
        return bool(logistics.loading_address or logistics.unloading_address)
