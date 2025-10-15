from pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from services.classifier import MailClassifier
from services.classifier import MailClassificationEnum
from pipeline.processing_context import ProcessingContext


class EmailClassificationStep(ProcessingStep):
    """Step for classifying emails using Gemini API"""

    def __init__(self, classifier: MailClassifier):
        super().__init__(ProcessingOrder.CLASSIFICATION)
        self.classifier = classifier

    def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Classify the email in the context

        Args:
            context: Processing context containing the email

        Returns:
            ProcessingResult with the classification
        """
        try:
            self.logger.info(f"Classifying email: {context.email.subject}")

            classification = self.classifier.classify_email(context.email)

            if classification:
                context.classification = classification
                self.logger.info(f"Email classified as: {classification}")
                return ProcessingResult(
                    success=True,
                    data={"classification": classification}
                )
            else:
                error_msg = "Classification returned None"
                self.logger.error(error_msg)
                return ProcessingResult(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"Failed to classify email: {str(e)}"
            self.logger.exception(error_msg)
            return ProcessingResult(
                success=False,
                error=error_msg
            )

    def should_process(self, context: ProcessingContext) -> bool:
        """
        Always process classification for new emails

        Args:
            context: Processing context

        Returns:
            True if classification should be attempted
        """
        return context.classification is None