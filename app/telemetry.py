"""
SRE RAG Agent — OpenTelemetry & Distributed Tracing Module (v4.0)
Configures OpenTelemetry TracerProvider, OTLP exporters, auto-instrumentation for
FastAPI, Asyncpg and Redis, and injects trace_id/span_id into structlog.
"""

import os
import structlog
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from config import settings

logger = structlog.get_logger()


def inject_otel_context(logger_instance, method_name, event_dict):
    """
    Structlog processor that extracts active OpenTelemetry trace context
    and injects trace_id and span_id into every log record.
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
        event_dict["span_id"] = trace.format_span_id(ctx.span_id)
    return event_dict


def setup_telemetry(app) -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry SDK and instrument core components.
    """
    try:
        resource = Resource.create(
            {
                "service.name": settings.app_name,
                "service.version": settings.app_version,
                "deployment.environment": "production" if settings.is_production else "development",
            }
        )

        tracer_provider = TracerProvider(resource=resource)

        # OTLP Exporter setup
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info("otel_otlp_exporter_configured", endpoint=otlp_endpoint)
            except Exception as e:
                logger.debug("otel_otlp_exporter_failed_fallback_console", error=str(e))
                tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(tracer_provider)

        # Auto-instrumentation
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
        try:
            AsyncPGInstrumentor().instrument()
        except Exception as exc:
            logger.debug("otel_asyncpg_instrumentation_skipped", error=str(exc))

        try:
            RedisInstrumentor().instrument()
        except Exception as exc:
            logger.debug("otel_redis_instrumentation_skipped", error=str(exc))

        logger.info("opentelemetry_tracing_initialized", service=settings.app_name)
        return trace.get_tracer(settings.app_name)

    except Exception as e:
        logger.warning("opentelemetry_initialization_skipped", error=str(e))
        return None
