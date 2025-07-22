# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from beeai_sdk import __version__

root_logger = logging.getLogger()


def configure_telemetry(app: FastAPI) -> None:
    """Utility that configures opentelemetry with OTLP exporter and FastAPI instrumentation"""

    FastAPIInstrumentor.instrument_app(app)

    resource = Resource(attributes={SERVICE_NAME: "beeai-sdk-a2a-server", SERVICE_VERSION: __version__})

    # Traces
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Metrics
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
    )
    metrics.set_meter_provider(meter_provider)

    # Logs
    logger_provider = LoggerProvider(resource=resource)
    processor = BatchLogRecordProcessor(OTLPLogExporter())
    logger_provider.add_log_record_processor(processor)
    root_logger.addHandler(LoggingHandler(logger_provider=logger_provider))
