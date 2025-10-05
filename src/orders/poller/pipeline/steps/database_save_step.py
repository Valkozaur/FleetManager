from ..processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from ...clients.google_sheets_client import GoogleSheetsClient
from ..processing_context import ProcessingContext


class DatabaseSaveStep(ProcessingStep):
    """Step for saving logistics data to Google Sheets"""

    def __init__(self, sheets_client: GoogleSheetsClient):
        super().__init__(ProcessingOrder.DATABASE_SAVE)
        self.sheets_client = sheets_client
        self.headers_initialized = False

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Save logistics data to Google Sheets

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

            # Initialize headers on first run
            if not self.headers_initialized:
                headers = self._get_headers()
                if not self.sheets_client.create_headers_if_not_exist(headers):
                    return ProcessingResult(
                        success=False,
                        error="Failed to create headers in spreadsheet"
                    )
                self.headers_initialized = True

            # Prepare data for saving
            data = self._prepare_data(context)
            headers = self._get_headers()

            # Save to Google Sheets
            if self.sheets_client.append_row(data, headers):
                self.logger.info(f"Successfully saved logistics data to Google Sheets for email: {context.email.subject}")
                return ProcessingResult(
                    success=True,
                    data={"saved_to_database": True}
                )
            else:
                return ProcessingResult(
                    success=False,
                    error="Failed to append row to Google Sheets"
                )

        except Exception as e:
            error_msg = f"Failed to save data to Google Sheets: {str(e)}"
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
            True if data should be saved to database
        """
        return context.has_logistics_data()

    def _get_headers(self) -> list[str]:
        """Get the column headers for the spreadsheet"""
        return [
            "email_id",
            "email_subject",
            "email_sender",
            "email_date",
            "loading_address",
            "unloading_address",
            "loading_date",
            "unloading_date",
            "loading_coordinates",
            "unloading_coordinates",
            "cargo_description",
            "weight",
            "vehicle_type",
            "special_requirements"
        ]

    def _prepare_data(self, context: ProcessingContext) -> dict:
        """
        Prepare data dictionary for saving to Google Sheets

        Args:
            context: Processing context containing logistics and email data

        Returns:
            Dictionary with data keyed by headers
        """
        logistics = context.logistics_data
        email = context.email

        # Update logistics data with email identifiers if not already present
        if not hasattr(logistics, 'email_id'):
            # Create updated logistics data with email identifiers
            from ...models.logistics import LogisticsDataExtract
            updated_logistics = LogisticsDataExtract(
                # Logistics fields
                loading_address=logistics.loading_address,
                unloading_address=logistics.unloading_address,
                loading_date=logistics.loading_date,
                unloading_date=logistics.unloading_date,
                loading_coordinates=logistics.loading_coordinates,
                unloading_coordinates=logistics.unloading_coordinates,
                cargo_description=logistics.cargo_description,
                weight=logistics.weight,
                vehicle_type=logistics.vehicle_type,
                special_requirements=logistics.special_requirements,
                # Email identifiers
                email_id=email.id,
                email_subject=email.subject,
                email_sender=email.sender,
                email_date=email.received_at
            )
            context.logistics_data = updated_logistics
            logistics = updated_logistics

        return {
            "email_id": logistics.email_id,
            "email_subject": logistics.email_subject,
            "email_sender": logistics.email_sender,
            "email_date": logistics.email_date.isoformat(),
            "loading_address": logistics.loading_address,
            "unloading_address": logistics.unloading_address,
            "loading_date": logistics.loading_date,
            "unloading_date": logistics.unloading_date,
            "loading_coordinates": logistics.loading_coordinates or "",
            "unloading_coordinates": logistics.unloading_coordinates or "",
            "cargo_description": logistics.cargo_description,
            "weight": logistics.weight,
            "vehicle_type": logistics.vehicle_type,
            "special_requirements": logistics.special_requirements or ""
        }