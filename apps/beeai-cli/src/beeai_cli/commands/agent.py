# Copyright 2025 IBM Corp.
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


import typer
from rich.table import Column

from acp import types, ServerNotification, RunAgentResult, McpError, ErrorData
from acp.types import AgentRunProgressNotification, AgentRunProgressNotificationParams
from beeai_cli.api import send_request, send_request_with_notifications
from beeai_cli.async_typer import AsyncTyper, console, err_console, create_table
from beeai_cli.utils import check_json

app = AsyncTyper()


@app.command("run")
async def run(
    name: str = typer.Argument(help="Name of the agent to call"),
    input: str = typer.Argument(help="Agent input as JSON", callback=check_json),
) -> None:
    """Call an agent with a given input."""
    text_streamed = False
    async for message in send_request_with_notifications(
        types.RunAgentRequest(method="agents/run", params=types.RunAgentRequestParams(name=name, input=input)),
        types.RunAgentResult,
    ):
        match message:
            case ServerNotification(
                root=AgentRunProgressNotification(params=AgentRunProgressNotificationParams(delta=delta))
            ):
                for log in filter(bool, delta.get("logs", [])):
                    if text := log.get("text", None):
                        err_console.print(f"Log: {text.strip()}")
                if text := delta.get("text", None):
                    console.print(text, end="")
                    text_streamed = True
            case RunAgentResult() as result:
                if not text_streamed:
                    if text := result.model_dump().get("output", {}).get("text", None):
                        console.print(text)
                    else:
                        console.print(result)
                else:
                    console.print()


@app.command("list")
async def list_agents():
    """List available agents"""
    result = await send_request(types.ListAgentsRequest(method="agents/list"), types.ListAgentsResult)
    extra_cols = ["ui"]
    with create_table(Column("Name", style="yellow"), *extra_cols, Column("Description", ratio=1)) as table:
        for agent in result.agents:
            table.add_row(
                agent.name,
                *[str(agent.model_extra.get(col, "<none>")) for col in extra_cols],
                agent.description,
            )
    console.print(table)


@app.command("info")
async def agent_detail(
    name: str = typer.Argument(help="Name of agent tool to show"),
):
    """Show details of an agent"""
    result = await send_request(types.ListAgentsRequest(method="agents/list"), types.ListAgentsResult)
    agents_by_name = {agent.name: agent for agent in result.agents}
    if not (agent := agents_by_name.get(name, None)):
        raise McpError(error=ErrorData(code=404, message=f"agent/{name} not found in any provider"))
    console.print(agent)
