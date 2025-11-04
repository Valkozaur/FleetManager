
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


def init_telemetry(service_name: str) -> None:
    """
    Initializes OpenTelemetry logging for the specified service.
    """
    resource = Resource.create({"service.name": service_name})
    
    # Create an OTLP log exporter
    exporter = OTLPLogExporter(insecure=True)
    
    # Create a logger provider
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    
    # Create a batch log record processor and add it to the logger provider
    processor = BatchLogRecordProcessor(exporter)
    logger_provider.add_log_record_processor(processor)
    
    # Add a handler to the root logger
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    
    # Set the overall logging level
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
