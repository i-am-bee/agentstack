import os
import sys


def serve():
    os.execv(
        sys.executable,
        [
            "python",
            "-m",
            "uvicorn",
            "beeai_server.application:app",
            "--host=0.0.0.0",
            "--port=8333",
            "--timeout-keep-alive=4",  # TODO: MCP server is not destroyed correctly
            "--timeout-graceful-shutdown=5",  # TODO: MCP server is not destroyed correctly
        ],
    )


__all__ = ["serve"]
