from typing import List, Optional
import logging

from .processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from .processing_context import ProcessingContext

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails"""
    pass


class ProcessingPipeline:
    """Orchestrates the execution of processing steps in order"""

    def __init__(self, steps: List[ProcessingStep]):
        """
        Initialize the pipeline with processing steps

        Args:
            steps: List of processing steps to execute in order
        """
        # Sort steps by their order
        self.steps = sorted(steps, key=lambda step: step.order)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validate that we have unique orders
        orders = [step.order for step in self.steps]
        if len(orders) != len(set(orders)):
            raise ValueError("Processing steps must have unique orders")

        self.logger.info(f"Initialized pipeline with {len(self.steps)} steps: {[str(step) for step in self.steps]}")

    def execute(self, context: ProcessingContext) -> ProcessingContext:
        """
        Execute all processing steps on the given context

        Args:
            context: The processing context containing the email to process

        Returns:
            Updated processing context with results from all steps

        Raises:
            PipelineExecutionError: If any critical step fails
        """
        self.logger.info(f"Starting pipeline execution for email: {context.email.subject}")

        for step in self.steps:
            try:
                self.logger.info(f"Executing step: {step}")

                # Check if step should be executed
                if not step.should_process(context):
                    self.logger.info(f"Skipping step {step} - should_process returned False")
                    continue

                # Execute the step
                result = step.process(context)

                if result.success:
                    context.mark_step_completed(step.__class__.__name__)
                    self.logger.info(f"Step {step} completed successfully")
                else:
                    error_msg = f"Step {step} failed: {result.error}"
                    context.add_error(error_msg, step.__class__.__name__)
                    self.logger.error(error_msg)

                    # For critical steps, we might want to stop execution
                    if self._is_critical_step(step):
                        raise PipelineExecutionError(error_msg)

            except Exception as e:
                error_msg = f"Unexpected error in step {step}: {str(e)}"
                context.add_error(error_msg, step.__class__.__name__)
                self.logger.exception(error_msg)

                # For critical steps, stop execution
                if self._is_critical_step(step):
                    raise PipelineExecutionError(error_msg) from e

        self.logger.info(f"Pipeline execution completed. Completed steps: {context.completed_steps}")
        return context

    def _is_critical_step(self, step: ProcessingStep) -> bool:
        """
        Determine if a step is critical (should stop pipeline on failure)

        Args:
            step: The processing step to check

        Returns:
            True if the step is critical, False otherwise
        """
        # Classification is critical - without it we can't proceed
        return step.order == ProcessingOrder.CLASSIFICATION

    def get_step_by_type(self, step_type: type) -> Optional[ProcessingStep]:
        """
        Get a step by its type

        Args:
            step_type: The type of step to find

        Returns:
            The step if found, None otherwise
        """
        for step in self.steps:
            if isinstance(step, step_type):
                return step
        return None

    def __str__(self) -> str:
        return f"ProcessingPipeline(steps={len(self.steps)})"

    def __repr__(self) -> str:
        return self.__str__()