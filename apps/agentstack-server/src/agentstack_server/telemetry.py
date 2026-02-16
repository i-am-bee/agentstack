# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from importlib.metadata import version

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, LogRecordExportResult
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricExportResult, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID, SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult

from agentstack_server.configuration import get_configuration
from agentstack_server.utils.id import generate_stable_id

root_logger = logging.getLogger()
logger = logging.getLogger(__name__)

OTEL_HTTP_ENDPOINT = str(get_configuration().telemetry.collector_url)

INSTRUMENTATION_NAME = "agentstack-server"

fastapi_instrumentor = FastAPIInstrumentor()
if fastapi_instrumentor:
    fastapi_instrumentor.instrument()

httpxclient_instrumentor = HTTPXClientInstrumentor()
if httpxclient_instrumentor:
    httpxclient_instrumentor.instrument()

openai_instrumentor = OpenAIInstrumentor()
if openai_instrumentor:
    openai_instrumentor.instrument()


class SilentOTLPSpanExporter(OTLPSpanExporter):
    def export(self, *args, **kwargs):
        try:
            return super().export(*args, **kwargs)
        except Exception as e:
            logger.debug(f"OpenTelemetry Exporter failed silently: {e}")
            return SpanExportResult.FAILURE


class SilentOTLPMetricExporter(OTLPMetricExporter):
    def export(self, *args, **kwargs):
        try:
            return super().export(*args, **kwargs)
        except Exception as e:
            logger.debug(f"OpenTelemetry Exporter failed silently: {e}")
            return MetricExportResult.FAILURE


class SilentOTLPLogExporter(OTLPLogExporter):
    def export(self, *args, **kwargs):
        try:
            return super().export(*args, **kwargs)
        except Exception as e:
            logger.debug(f"OpenTelemetry Exporter failed silently: {e}")
            return LogRecordExportResult.FAILURE


def configure_telemetry():
    resource = Resource(
        attributes={
            SERVICE_NAME: "agentstack-server",
            SERVICE_VERSION: version("agentstack-server"),
            SERVICE_INSTANCE_ID: generate_stable_id(),
        }
    )
    trace.set_tracer_provider(
        tracer_provider=TracerProvider(
            resource=resource,
            # pyrefly: ignore [bad-argument-type] TODO: active_span_processor explicitly allows only certain span processors, is that an issue?
            active_span_processor=BatchSpanProcessor(SilentOTLPSpanExporter(endpoint=OTEL_HTTP_ENDPOINT + "v1/traces")),
        )
    )
    metrics.set_meter_provider(
        MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(SilentOTLPMetricExporter(endpoint=OTEL_HTTP_ENDPOINT + "v1/metrics"))
            ],
        )
    )
    logger_provider = LoggerProvider(resource=resource)
    processor = BatchLogRecordProcessor(SilentOTLPLogExporter(endpoint=OTEL_HTTP_ENDPOINT + "v1/logs"))
    logger_provider.add_log_record_processor(processor)
    root_logger.addHandler(LoggingHandler(logger_provider=logger_provider))


def shutdown_telemetry():
    tracer_provider = trace.get_tracer_provider()
    if isinstance(tracer_provider, TracerProvider):
        tracer_provider.shutdown()

    meter_provider = metrics.get_meter_provider()
    if isinstance(meter_provider, MeterProvider):
        meter_provider.shutdown()
