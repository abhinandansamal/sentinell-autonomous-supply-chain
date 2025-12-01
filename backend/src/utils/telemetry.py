from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, Tracer
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_telemetry(service_name: str) -> Tracer:
    """
    Configures the OpenTelemetry (OTel) infrastructure for the application.

    This setup initializes the Global Tracer Provider, which acts as the factory
    for creating 'Spans' (records of operations).

    For this local development environment, we use the ConsoleSpanExporter.
    This means trace data will be printed to Standard Output (stdout), allowing
    us to verify visibility without needing a complex backend like Jaeger or Zipkin.

    Args:
        service_name (str): The identifier for this service (e.g., 'sentinell-backend').
                            This helps filter logs in a microservices environment.

    Returns:
        Tracer: An initialized OTel tracer instance ready for manual instrumentation.
    """
    # 1. Define the Resource
    # This adds metadata to every trace (Service Name, Version, etc.)
    resource = Resource.create(attributes={
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "development"
    })

    # 2. Initialize the Tracer Provider
    # The Provider holds the configuration for how traces are processed.
    provider = TracerProvider(resource=resource)

    # 3. Configure the Exporter
    # We use ConsoleSpanExporter to dump traces to the terminal for verification.
    # In production, you would swap this for OTLPSpanExporter (to Google Cloud Trace).
    console_exporter = ConsoleSpanExporter()
    
    # 4. Add the Processor
    # BatchSpanProcessor buffers spans and sends them in chunks to improve performance.
    processor = BatchSpanProcessor(console_exporter)
    provider.add_span_processor(processor)

    # 5. Set the Global Provider
    # This ensures that libraries like FastAPI can automatically find this config.
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(service_name)