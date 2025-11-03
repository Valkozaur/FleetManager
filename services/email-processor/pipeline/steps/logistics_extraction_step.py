from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from services.logistics_data_extract import LogisticsDataExtractor
from pipeline.processing_context import ProcessingContext


class LogisticsExtractionStep(ProcessingStep):
    """Step for extracting logistics data from order emails using Gemini API"""

    def __init__(self, extractor: LogisticsDataExtractor):
        super().__init__(ProcessingOrder.LOGISTICS_EXTRACTION)
        self.extractor = extractor

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Extract logistics data from the email in the context

        Args:
            context: Processing context containing the classified email

        Returns:
            ProcessingResult with the extracted logistics data
        """
        try:
            self.logger.info(f"Extracting logistics data from email: {context.email.subject}")

            logistics_data = self.extractor.extract_logistics_data(context.email)

            if logistics_data:
                context.logistics_data = logistics_data
                self.logger.info(f"Successfully extracted logistics data")
                return ProcessingResult(
                    success=True,
                    data={"logistics_data": logistics_data}
                )
            else:
                error_msg = "Logistics data extraction returned None"
                self.logger.warning(error_msg)
                return ProcessingResult(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"Failed to extract logistics data: {str(e)}"
            self.logger.exception(error_msg)
            return ProcessingResult(
                success=False,
                error=error_msg
            )

    def should_process(self, context: ProcessingContext) -> bool:
        """
        Only process logistics extraction for order emails that haven't been processed yet

        Args:
            context: Processing context

        Returns:
            True if logistics extraction should be attempted
        """
        return (
            context.is_order_email() and
            not context.has_logistics_data() and
            context.classification is not None
        )