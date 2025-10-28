import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def configure_opentelemetry():
    """
    Configures OpenTelemetry for the application.
    """
    service_name = os.environ.get("OTEL_SERVICE_NAME", "email-processor")
    resource = Resource(attributes={
        "service.name": service_name,
    })

    # Set up a TracerProvider and BatchSpanProcessor
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Configure the OTLP exporter
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    
    # Add the exporter to the provider
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    # Instrument libraries
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument()

    print("OpenTelemetry configured")
