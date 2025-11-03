"""
PostgreSQL Save Step - Saves logistics data to PostgreSQL database
"""

from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from clients.database_client import DatabaseClient
from pipeline.processing_context import ProcessingContext


class PostgresSaveStep(ProcessingStep):
    """Step for saving logistics data to PostgreSQL database"""

    def __init__(self, db_client: DatabaseClient):
        """
        Initialize the PostgreSQL save step

        Args:
            db_client: DatabaseClient instance for database operations
        """
        super().__init__(ProcessingOrder.POSTGRES_SAVE)
        self.db_client = db_client

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Save logistics data to PostgreSQL database

        Args:
            context: Processing context containing the logistics data

        Returns:
            ProcessingResult indicating success or failure
        """
        try:
            if not context.has_logistics_data():
                return ProcessingResult(
                    success=False,
                    error="No logistics data to save"
                )

            logistics_data = context.logistics_data

            # Ensure email metadata is populated
            if not logistics_data.email_id:
                logistics_data.email_id = context.email.id
            if not logistics_data.email_subject:
                logistics_data.email_subject = context.email.subject
            if not logistics_data.email_sender:
                logistics_data.email_sender = context.email.sender
            if not logistics_data.email_date:
                logistics_data.email_date = context.email.received_at
            if not logistics_data.polled_at:
                logistics_data.polled_at = context.start_time

            # Save to PostgreSQL
            order_id = self.db_client.save_order(logistics_data)

            if order_id:
                self.logger.info(
                    f"Successfully saved logistics data to PostgreSQL with ID {order_id} "
                    f"for email: {context.email.subject}"
                )
                return ProcessingResult(
                    success=True,
                    data={"order_id": order_id, "saved_to_postgres": True}
                )
            else:
                return ProcessingResult(
                    success=False,
                    error="Failed to save order to PostgreSQL"
                )

        except Exception as e:
            error_msg = f"Failed to save data to PostgreSQL: {str(e)}"
            self.logger.exception(error_msg)
            return ProcessingResult(
                success=False,
                error=error_msg
            )

    def should_process(self, context: ProcessingContext) -> bool:
        """
        Only save data for emails that have logistics data

        Args:
            context: Processing context

        Returns:
            True if data should be saved to PostgreSQL
        """
        return context.has_logistics_data()
