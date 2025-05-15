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

import kr8s
import typer

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.commands.platform import HelmChart, KUBECONFIG
from beeai_cli.utils import get_telemetry_config, save_telemetry_config

app = AsyncTyper()


@app.command("sharing")
async def sharing(disable: bool | None = typer.Option(None, help="Disable sharing")):
    """Read and update telemetry sharing configuration."""
    telemetry_config = get_telemetry_config()
    if disable is not None:
        sharing_enabled = not disable
        if sharing_enabled != telemetry_config["sharing"]:
            save_telemetry_config(False)
            helm_chart = HelmChart(
                {"metadata": {"name": "beeai", "namespace": "default"}},
                api=await kr8s.asyncio.api(kubeconfig=KUBECONFIG),
            )
            if await helm_chart.exists():
                await helm_chart.patch({"spec": {"set": {"telemetry.sharing": str(sharing_enabled).lower()}}})
    console.print(get_telemetry_config())
