import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.pipeline.pipeline import ProcessingPipeline, PipelineExecutionError
from src.pipeline.processing_step import ProcessingStep, ProcessingResult, ProcessingOrder
from src.pipeline.processing_context import ProcessingContext
from src.models.email import Email


class MockProcessingStep(ProcessingStep):
    """Mock processing step for testing"""

    def __init__(self, order: ProcessingOrder, should_process_result=True,
                 process_result=None, raise_exception=None):
        super().__init__(order)
        self.should_process_result = should_process_result
        self.process_result = process_result if process_result is not None else ProcessingResult(success=True)
        self.raise_exception = raise_exception
        self.process_call_count = 0
        self.should_process_call_count = 0

    def process(self, context: ProcessingContext) -> ProcessingResult:
        self.process_call_count += 1
        if self.raise_exception:
            raise self.raise_exception
        return self.process_result

    def should_process(self, context: ProcessingContext) -> bool:
        self.should_process_call_count += 1
        return self.should_process_result


class MockClassificationStep(MockProcessingStep):
    """Mock classification step (order 1)"""
    def __init__(self, should_process_result=True, process_result=None, raise_exception=None):
        super().__init__(ProcessingOrder.CLASSIFICATION, should_process_result, process_result, raise_exception)


class MockLogisticsStep(MockProcessingStep):
    """Mock logistics extraction step (order 2)"""
    def __init__(self, should_process_result=True, process_result=None, raise_exception=None):
        super().__init__(ProcessingOrder.LOGISTICS_EXTRACTION, should_process_result, process_result, raise_exception)


class MockGeocodingStep(MockProcessingStep):
    """Mock geocoding step (order 3)"""
    def __init__(self, should_process_result=True, process_result=None, raise_exception=None):
        super().__init__(ProcessingOrder.GEOCODING, should_process_result, process_result, raise_exception)


@pytest.fixture
def sample_email():
    """Create a sample email for testing"""
    return Email(
        id="test_email_123",
        subject="Test Order Email",
        sender="test@example.com",
        body="This is a test order email",
        received_at=datetime.now()
    )


@pytest.fixture
def sample_context(sample_email):
    """Create a sample processing context"""
    return ProcessingContext(email=sample_email)


class TestProcessingPipeline:
    """Test cases for ProcessingPipeline class"""

    def test_initialization_with_valid_steps(self):
        """Test pipeline initialization with valid steps in random order"""
        steps = [
            MockGeocodingStep(),
            MockClassificationStep(),
            MockLogisticsStep()
        ]

        pipeline = ProcessingPipeline(steps)

        assert len(pipeline.steps) == 3
        assert pipeline.steps[0].order == ProcessingOrder.CLASSIFICATION
        assert pipeline.steps[1].order == ProcessingOrder.LOGISTICS_EXTRACTION
        assert pipeline.steps[2].order == ProcessingOrder.GEOCODING

    def test_initialization_with_duplicate_orders(self):
        """Test pipeline initialization fails with duplicate step orders"""
        steps = [
            MockClassificationStep(),
            MockClassificationStep()  # Duplicate order
        ]

        with pytest.raises(ValueError, match="Processing steps must have unique orders"):
            ProcessingPipeline(steps)

    def test_initialization_with_empty_steps(self):
        """Test pipeline initialization with no steps"""
        pipeline = ProcessingPipeline([])
        assert len(pipeline.steps) == 0

    def test_str_representation(self):
        """Test string representation of pipeline"""
        steps = [MockClassificationStep(), MockLogisticsStep()]
        pipeline = ProcessingPipeline(steps)

        assert str(pipeline) == "ProcessingPipeline(steps=2)"
        assert repr(pipeline) == "ProcessingPipeline(steps=2)"

    def test_execute_all_steps_success(self, sample_context):
        """Test successful execution of all steps"""
        classification_step = MockClassificationStep()
        logistics_step = MockLogisticsStep()
        geocoding_step = MockGeocodingStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step, geocoding_step])

        result = pipeline.execute(sample_context)

        assert result == sample_context
        assert classification_step.process_call_count == 1
        assert logistics_step.process_call_count == 1
        assert geocoding_step.process_call_count == 1
        assert len(result.completed_steps) == 3
        assert "MockClassificationStep" in result.completed_steps
        assert "MockLogisticsStep" in result.completed_steps
        assert "MockGeocodingStep" in result.completed_steps
        assert len(result.errors) == 0

    def test_execute_step_skipped_when_should_process_false(self, sample_context):
        """Test step is skipped when should_process returns False"""
        classification_step = MockClassificationStep(should_process_result=True)
        logistics_step = MockLogisticsStep(should_process_result=False)
        geocoding_step = MockGeocodingStep(should_process_result=True)

        pipeline = ProcessingPipeline([classification_step, logistics_step, geocoding_step])

        result = pipeline.execute(sample_context)

        assert classification_step.process_call_count == 1
        assert logistics_step.process_call_count == 0  # Not processed
        assert geocoding_step.process_call_count == 1
        assert len(result.completed_steps) == 2
        assert "MockLogisticsStep" not in result.completed_steps

    def test_execute_non_critical_step_failure_continues(self, sample_context):
        """Test pipeline continues when non-critical step fails"""
        classification_step = MockClassificationStep()
        logistics_step = MockLogisticsStep(
            process_result=ProcessingResult(success=False, error="Logistics failed")
        )
        geocoding_step = MockGeocodingStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step, geocoding_step])

        result = pipeline.execute(sample_context)

        assert len(result.completed_steps) == 2  # Classification and Geocoding only
        assert "MockClassificationStep" in result.completed_steps
        assert "MockGeocodingStep" in result.completed_steps
        assert "MockLogisticsStep" not in result.completed_steps  # Failed step not marked as completed
        assert len(result.errors) == 1
        assert "Logistics failed" in result.errors[0]
        assert "MockLogisticsStep" in result.failed_steps
        assert geocoding_step.process_call_count == 1  # Still executed

    def test_execute_critical_step_failure_stops_pipeline(self, sample_context):
        """Test pipeline stops when critical step fails"""
        classification_step = MockClassificationStep(
            process_result=ProcessingResult(success=False, error="Classification failed")
        )
        logistics_step = MockLogisticsStep()
        geocoding_step = MockGeocodingStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step, geocoding_step])

        with pytest.raises(PipelineExecutionError, match="Unexpected error in step"):
            pipeline.execute(sample_context)

        assert classification_step.process_call_count == 1
        assert logistics_step.process_call_count == 0  # Not executed
        assert geocoding_step.process_call_count == 0  # Not executed
        assert len(sample_context.completed_steps) == 0
        # The pipeline adds 2 errors: one for the failure, one for the caught exception
        assert len(sample_context.errors) == 2
        assert "Classification failed" in sample_context.errors[0]
        assert "Unexpected error in step" in sample_context.errors[1]

    def test_execute_unexpected_exception_in_critical_step(self, sample_context):
        """Test pipeline stops on unexpected exception in critical step"""
        classification_step = MockClassificationStep(
            raise_exception=RuntimeError("Unexpected error")
        )
        logistics_step = MockLogisticsStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step])

        with pytest.raises(PipelineExecutionError, match="Unexpected error"):
            pipeline.execute(sample_context)

        assert logistics_step.process_call_count == 0  # Not executed

    def test_execute_unexpected_exception_in_non_critical_step(self, sample_context):
        """Test pipeline continues on unexpected exception in non-critical step"""
        classification_step = MockClassificationStep()
        logistics_step = MockLogisticsStep(
            raise_exception=RuntimeError("Unexpected error")
        )
        geocoding_step = MockGeocodingStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step, geocoding_step])

        result = pipeline.execute(sample_context)

        assert classification_step.process_call_count == 1
        assert logistics_step.process_call_count == 1
        assert geocoding_step.process_call_count == 1  # Still executed
        assert len(result.errors) == 1
        assert "Unexpected error" in result.errors[0]

    def test_get_step_by_type_found(self):
        """Test get_step_by_type returns correct step when found"""
        classification_step = MockClassificationStep()
        logistics_step = MockLogisticsStep()

        pipeline = ProcessingPipeline([classification_step, logistics_step])

        result = pipeline.get_step_by_type(MockClassificationStep)
        assert result == classification_step

        result = pipeline.get_step_by_type(MockLogisticsStep)
        assert result == logistics_step

    def test_get_step_by_type_not_found(self):
        """Test get_step_by_type returns None when step type not found"""
        classification_step = MockClassificationStep()

        pipeline = ProcessingPipeline([classification_step])

        result = pipeline.get_step_by_type(MockLogisticsStep)
        assert result is None

    def test_is_critical_step_classification(self):
        """Test that classification step is identified as critical"""
        classification_step = MockClassificationStep()
        pipeline = ProcessingPipeline([classification_step])

        assert pipeline._is_critical_step(classification_step) is True

    def test_is_critical_step_non_classification(self):
        """Test that non-classification steps are not critical"""
        logistics_step = MockLogisticsStep()
        geocoding_step = MockGeocodingStep()

        pipeline = ProcessingPipeline([logistics_step, geocoding_step])

        assert pipeline._is_critical_step(logistics_step) is False
        assert pipeline._is_critical_step(geocoding_step) is False

    @patch('src.orders.poller.pipeline.pipeline.logging.getLogger')
    def test_logging_initialization(self, mock_get_logger):
        """Test that logger is properly initialized"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        steps = [MockClassificationStep()]
        pipeline = ProcessingPipeline(steps)

        # Verify logger was called with class name
        mock_get_logger.assert_called_with('ProcessingPipeline')
        # Verify initialization was logged
        mock_logger.info.assert_called_once()
        assert "Initialized pipeline with 1 steps" in mock_logger.info.call_args[0][0]

    @patch('src.orders.poller.pipeline.pipeline.logging.getLogger')
    def test_logging_execution(self, mock_get_logger):
        """Test that execution is properly logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        steps = [MockClassificationStep()]
        pipeline = ProcessingPipeline(steps)
        pipeline.logger = mock_logger  # Replace the logger

        sample_context = ProcessingContext(
            email=Email(
                id="test",
                subject="Test Subject",
                sender="test@example.com",
                body="Test body",
                received_at=datetime.now()
            )
        )

        pipeline.execute(sample_context)

        # Verify execution start and completion were logged
        assert mock_logger.info.call_count >= 3  # Start, step execution, completion