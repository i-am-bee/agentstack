# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from importlib.metadata import version
import logging

from beeai_server.configuration import get_configuration
from beeai_server.utils.id import generate_stable_id
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, SERVICE_INSTANCE_ID
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


logger = logging.getLogger(__name__)

OTEL_HTTP_ENDPOINT = str(get_configuration().telemetry.collector_url)

INSTRUMENTATION_NAME = "beeai-server"


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
            return SpanExportResult.FAILURE


def configure_telemetry():
    resource = Resource(
        attributes={
            SERVICE_NAME: "beeai-server",
            SERVICE_VERSION: version("beeai-server"),
            SERVICE_INSTANCE_ID: generate_stable_id(),
        }
    )
    trace.set_tracer_provider(
        tracer_provider=TracerProvider(
            resource=resource,
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


def shutdown_telemetry():
    tracer_provider = trace.get_tracer_provider()
    if isinstance(tracer_provider, TracerProvider):
        tracer_provider.shutdown()

    meter_provider = metrics.get_meter_provider()
    if isinstance(meter_provider, MeterProvider):
        meter_provider.shutdown()
