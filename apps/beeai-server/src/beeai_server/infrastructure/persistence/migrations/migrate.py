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

from datetime import timedelta
from pathlib import Path

from tenacity import retry, wait_fixed, stop_after_delay

from beeai_server import logger

migrations_path = Path(__file__).parent.resolve()


@retry(stop=stop_after_delay(timedelta(minutes=10)), wait=wait_fixed(2), reraise=True)
def _wait_for_db(alembic_cfg):
    from alembic import command

    logger.info("Waiting for database to be ready...")

    command.show(alembic_cfg, "current")


def migrate(wait_for_db: bool = True):
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(migrations_path / "alembic.ini")
    orig_script_location = alembic_cfg.get_main_option("script_location")
    alembic_cfg.set_main_option("script_location", str(migrations_path / orig_script_location))
    if wait_for_db:
        _wait_for_db(alembic_cfg)

    command.upgrade(alembic_cfg, "head")
