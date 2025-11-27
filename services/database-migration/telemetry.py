
import logging
import os


def init_telemetry(service_name: str) -> None:
    """
    Initializes OpenTelemetry logging for the specified service.
    Gracefully degrades if OTLP endpoint is not available.
    """
    # Set up basic console logging first (always works)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    
    # Only initialize OTLP if endpoint is configured
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping OpenTelemetry initialization")
        return
    
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
        
        resource = Resource.create({"service.name": service_name})
        
        # Create an OTLP log exporter with short timeout
        exporter = OTLPLogExporter(insecure=True, timeout=5)
        
        # Create a logger provider
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)
        
        # Create a batch log record processor with shorter export interval
        processor = BatchLogRecordProcessor(
            exporter,
            max_export_batch_size=512,
            schedule_delay_millis=1000,  # Export every 1 second instead of 5
            export_timeout_millis=5000,  # 5 second timeout
        )
        logger_provider.add_log_record_processor(processor)
        
        # Add a handler to the root logger
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        
        logger.info(f"OpenTelemetry initialized with endpoint: {otel_endpoint}")
        
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}. Continuing without telemetry.")
