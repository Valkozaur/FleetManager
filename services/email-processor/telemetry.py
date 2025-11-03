import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.metrics import set_meter_provider, get_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

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

    # Configure the OTLP exporter for traces
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    
    # Add the exporter to the provider
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    # Set up a MeterProvider and PeriodicExportingMetricReader
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    set_meter_provider(meter_provider)

    # Instrument libraries
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument()

    print("OpenTelemetry configured")
