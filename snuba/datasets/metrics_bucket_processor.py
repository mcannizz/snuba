from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional

from snuba import settings
from snuba.consumers.types import KafkaMessageMetadata
from snuba.datasets.events_format import EventTooOld, enforce_retention
from snuba.datasets.metrics_aggregate_processor import (
    METRICS_COUNTERS_TYPE,
    METRICS_DISTRIBUTIONS_TYPE,
    METRICS_SET_TYPE,
)
from snuba.processor import (
    InsertBatch,
    MessageProcessor,
    ProcessedMessage,
    _ensure_valid_date,
)

DISABLED_MATERIALIZATION_VERSION = 1


class MetricsBucketProcessor(MessageProcessor, ABC):
    @abstractmethod
    def _should_process(self, message: Mapping[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _process_values(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    def process_message(
        self, message: Mapping[str, Any], metadata: KafkaMessageMetadata
    ) -> Optional[ProcessedMessage]:
        # TODO: Support messages with multiple buckets

        if not self._should_process(message):
            return None

        timestamp = _ensure_valid_date(datetime.utcfromtimestamp(message["timestamp"]))
        assert timestamp is not None

        keys = []
        values = []
        tags = message["tags"]
        assert isinstance(tags, Mapping)
        for key, value in sorted(tags.items()):
            assert key.isdigit()
            keys.append(int(key))
            assert isinstance(value, int)
            values.append(value)

        mat_version = (
            DISABLED_MATERIALIZATION_VERSION
            if settings.WRITE_METRICS_AGG_DIRECTLY
            else settings.ENABLED_MATERIALIZATION_VERSION
        )

        try:
            retention_days = enforce_retention(message["retention_days"], timestamp)
        except EventTooOld:
            return None

        processed = {
            "org_id": message["org_id"],
            "project_id": message["project_id"],
            "metric_id": message["metric_id"],
            "timestamp": timestamp,
            "tags.key": keys,
            "tags.value": values,
            **self._process_values(message),
            "materialization_version": mat_version,
            "retention_days": retention_days,
            "partition": metadata.partition,
            "offset": metadata.offset,
        }
        return InsertBatch([processed], None)


class SetsMetricsProcessor(MetricsBucketProcessor):
    def _should_process(self, message: Mapping[str, Any]) -> bool:
        return message["type"] is not None and message["type"] == "s"

    def _process_values(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        values = message["value"]
        for v in values:
            assert isinstance(v, int), "Illegal value in set. Int expected: {v}"
        return {"set_values": values}


class CounterMetricsProcessor(MetricsBucketProcessor):
    def _should_process(self, message: Mapping[str, Any]) -> bool:
        return message["type"] is not None and message["type"] == "c"

    def _process_values(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        value = message["value"]
        assert isinstance(
            value, (int, float)
        ), "Illegal value for counter value. Int/Float expected {value}"
        return {"value": value}


class DistributionsMetricsProcessor(MetricsBucketProcessor):
    def _should_process(self, message: Mapping[str, Any]) -> bool:
        return message["type"] is not None and message["type"] == "d"

    def _process_values(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        values = message["value"]
        for v in values:
            assert isinstance(
                v, (int, float)
            ), "Illegal value in set. Int expected: {v}"
        return {"values": values}


class OutputType(Enum):
    SET = "set"
    COUNTER = "counter"
    DIST = "distribution"


class PolymorphicMetricsProcessor(MetricsBucketProcessor):
    def _should_process(self, message: Mapping[str, Any]) -> bool:
        return message["type"] in {
            METRICS_SET_TYPE,
            METRICS_COUNTERS_TYPE,
            METRICS_DISTRIBUTIONS_TYPE,
        }

    def _process_values(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        if message["type"] == METRICS_SET_TYPE:
            values = message["value"]
            for v in values:
                assert isinstance(v, int), "Illegal value in set. Int expected: {v}"
            return {"metric_type": OutputType.SET.value, "set_values": values}
        elif message["type"] == METRICS_COUNTERS_TYPE:
            value = message["value"]
            assert isinstance(
                value, (int, float)
            ), "Illegal value for counter value. Int/Float expected {value}"
            return {"metric_type": OutputType.COUNTER.value, "count_value": value}
        else:  # METRICS_DISTRIBUTIONS_TYPE
            values = message["value"]
            for v in values:
                assert isinstance(
                    v, (int, float)
                ), "Illegal value in set. Int expected: {v}"
            return {"metric_type": OutputType.DIST.value, "distribution_values": values}
