# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import pathlib
import shlex
from collections.abc import Awaitable, Callable, Mapping
from inspect import signature
from typing import Any, Literal, get_overloads, overload

logger = logging.getLogger("kubectl")


class Kubectl:
    """
    A dumb wrapper around the `kubectl` CLI. It depends on the `kubectl` binary being available in the PATH.
    Unlike the official and unofficial Python clients for Kubernetes, this wrapper is both async and fully supports `kubectl exec`.

    The sub-command of `kubectl` translates to method name, the rest of the arguments are passed as string arguments:
    `kubectl.exec("my-pod", "--", "ls", "-l")` -> `kubectl exec my-pod -- ls -l`

    Keyword arguments are passed as `--key=value` or `--key` if the value is `True`:
    `kubectl.delete("pod", "my-pod", now=True, grace_period=0)` -> `kubectl delete pod my-pod --now --grace-period=0`

    For commands that support JSON, `--output=json` is automatically added and the output is parsed and returned as a Python dict:
    `kubectl.get("pod", "my-pod")` -> `kubectl get pod my-pod --output=json`

    As a special case, `exec_raw` is provided to run a command and get the `asyncio.subprocess.Process` object back. This is useful for streaming data to/from the process.

    The keyword arguments passed to the constructor are used as default arguments for all commands. Useful for setting the namespace or context.
    """

    _default_kwargs: dict[str, str | bool]

    def __init__(self, **kwargs: str | bool | pathlib.Path | None):
        self._default_kwargs = self._fix_kwargs(kwargs)

    def _fix_kwargs(self, kwargs: Mapping[str, str | bool | pathlib.Path | None]) -> dict[str, str | bool]:
        return {
            key.removeprefix("_"): str(value) if isinstance(value, pathlib.Path) else value
            for key, value in kwargs.items()
            if value
        }

    async def _spawn_process(self, *args: str, **kwargs: str | bool) -> asyncio.subprocess.Process:
        dashdash_position = next((i for i, arg in enumerate(args) if arg == "--"), len(args))
        all_args = (
            list(args[:dashdash_position])
            + [
                (f"--{key}={value}" if value is not True else f"--{key}")
                for key, value in (self._default_kwargs | self._fix_kwargs(kwargs)).items()
            ]
            + list(args[dashdash_position:])
        )
        logger.info("kubectl %s", shlex.join(all_args))
        return await asyncio.create_subprocess_exec(
            "kubectl",
            *all_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _command(
        self,
        *args: str,
        input: bytes | str | list | dict | None = None,
        **kwargs: str | bool,
    ) -> str:
        process = await self._spawn_process(*args, **kwargs)
        if input and process.stdin:
            if isinstance(input, (list, dict)):
                input = json.dumps(input)
            if isinstance(input, str):
                input = input.encode()
            process.stdin.write(input)
            process.stdin.write_eof()
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Error ({process.returncode}) running kubectl command: {stderr.decode()}")
        return stdout.decode()

    @overload
    def __getattr__(
        self,
        name: Literal[
            "annotate",
            "apply",
            "autoscale",
            "create",
            "edit",
            "events",
            "expose",
            "get",
            "label",
            "patch",
            "replace",
            "run",
            "scale",
            "taint",
            "version",
            "wait",
        ],
    ) -> Callable[..., Awaitable[dict]]:
        async def command_json(
            *args: str,
            input: bytes | str | list | dict | None = None,
            **kwargs: str | bool | None,
        ) -> dict:
            output_str = await self._command(name.replace("_", "-"), *args, input=input, output="json", **kwargs)
            return json.loads(output_str)

        return command_json

    @overload
    def __getattr__(
        self,
        name: Literal[
            "api_resources",
            "api_versions",
            "attach",
            "auth",
            "certificate",
            "cluster_info",
            "completion",
            "config",
            "cordon",
            "cp",
            "ctx",
            "debug",
            "delete",
            "describe",
            "diff",
            "drain",
            "exec",
            "explain",
            "help",
            "kustomize",
            "logs",
            "ns",
            "options",
            "plugin",
            "port_forward",
            "proxy",
            "rollout",
            "set",
            "top",
            "uncordon",
        ],
    ) -> Callable[..., Awaitable[str]]:
        async def command(
            *args: str,
            input: bytes | str | list | dict | None = None,
            **kwargs: str | bool | None,
        ) -> str:
            return await self._command(name.replace("_", "-"), *args, input=input, **kwargs)

        return command

    def __getattr__(self, name: str) -> Callable[..., Awaitable[Any]]:
        getattr_overloads = get_overloads(self.__getattr__)
        for getattr_overload in getattr_overloads:
            if name in signature(getattr_overload).parameters["name"].annotation.__args__:
                return getattr_overload(self, name)  # type: ignore
        raise AttributeError(f"Command {name} not found")

    async def exec_raw(self, *args, **kwargs: str | bool) -> asyncio.subprocess.Process:
        return await self._spawn_process("exec", *args, **kwargs)
