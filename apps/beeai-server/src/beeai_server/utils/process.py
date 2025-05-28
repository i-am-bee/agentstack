# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import anyio
import anyio.abc
import anyio.to_thread

logger = logging.getLogger(__name__)


async def find_free_port() -> int:
    """Get a random free port assigned by the OS."""
    listener = await anyio.create_tcp_listener()
    port = listener.extra(anyio.abc.SocketAttribute.local_address)[1]
    await listener.aclose()
    return port
