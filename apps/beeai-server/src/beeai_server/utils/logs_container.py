# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Callable, Iterable, AsyncIterator

import anyio
from anyio import WouldBlock
from pydantic import BaseModel, Field

from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class ProcessLogType(StrEnum):
    stdout = "stdout"
    stderr = "stderr"


class ProcessLogMessage(BaseModel, extra="allow"):
    stream: ProcessLogType
    message: str
    time: datetime = Field(default_factory=utc_now)


class LogsContainer:
    def __init__(self, max_lines: int = 500):
        self._logs: deque[ProcessLogMessage] = deque(maxlen=max_lines)
        self._subscribers: set[Callable[[ProcessLogMessage], None]] = set()
        self._max_lines = max_lines

    def clear(self):
        self._logs.clear()

    def _notify_subscribers(self, log: ProcessLogMessage):
        for subscriber in self._subscribers:
            subscriber(log)

    def add(self, log: ProcessLogMessage):
        self._logs.append(log)
        self._notify_subscribers(log)

    def add_stdout(self, text: str):
        self.add(ProcessLogMessage(stream=ProcessLogType.stdout, message=text.rstrip("\n\r")))

    def add_stderr(self, text: str):
        self.add(ProcessLogMessage(stream=ProcessLogType.stdout, message=text.rstrip("\n\r")))

    def subscribe(self, handler: Callable[[ProcessLogMessage], None]):
        self._subscribers.add(handler)

    def unsubscribe(self, handler: Callable[[ProcessLogMessage], None]):
        self._subscribers.remove(handler)

    @property
    def logs(self) -> Iterable[ProcessLogMessage]:
        return self._logs

    @property
    def stdout(self) -> list[str]:
        return [log.message for log in self._logs if log.stream == ProcessLogType.stdout]

    @property
    def stderr(self) -> list[str]:
        return [log.message for log in self._logs if log.stream == ProcessLogType.stderr]

    @asynccontextmanager
    async def stream(
        self, include_old: bool = True, max_buffer_size: int | None = None
    ) -> AsyncIterator[AsyncIterator[ProcessLogMessage]]:
        max_buffer_size = max_buffer_size or self._max_lines * 2
        stream_send, stream_receive = anyio.create_memory_object_stream(max_buffer_size=max_buffer_size)

        def _handle_message(log: ProcessLogMessage):
            try:
                stream_send.send_nowait(log)
            except WouldBlock:
                logger.debug("Unable to stream logs to client due to a full buffer")

        if include_old:
            for message in self.logs:
                stream_send.send_nowait(message)

        try:
            self.subscribe(_handle_message)
            yield stream_receive
        finally:
            self.unsubscribe(_handle_message)
