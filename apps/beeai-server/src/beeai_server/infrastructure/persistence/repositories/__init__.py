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

logger = logging.getLogger(__name__)


def import_repositories():
    """Import all repositories to make sure they are registered into sqlalchemy metadata"""
    import importlib
    import pkgutil

    for _, name, _ in pkgutil.walk_packages(__path__):
        importlib.import_module(f"{__name__}.{name}")
        logger.debug(f"Discovered repository: {__name__}.{name}")


import_repositories()
