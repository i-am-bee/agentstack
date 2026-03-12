# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import re
import typing

import anyio
import typer

from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.console import console
from agentstack_cli.utils import run_command, verbosity

app = AsyncTyper()

# The in-cluster registry DNS name (used in pod image references)
REGISTRY_INTERNAL = "registry.cr-system.svc.cluster.local:5000"
# NodePort exposed by the post-renderer (matches registries.conf mirror)
REGISTRY_NODEPORT = 30500


@app.command("build")
async def build_agent(
    context: typing.Annotated[str, typer.Argument(help="Docker build context (path or URL)")] = ".",
    dockerfile: typing.Annotated[str | None, typer.Option("-f", "--dockerfile", help="Dockerfile path")] = None,
    tag: typing.Annotated[str | None, typer.Option("-t", "--tag", help="Image tag (default: auto-generated)")] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
) -> None:
    """Build an agent image locally and push it to the platform registry. [Local only]"""
    with verbosity(verbose):
        dockerfile_args = ("-f", dockerfile) if dockerfile else ()

        # Derive a short image name if tag not provided
        if not tag:
            context_hash = hashlib.sha256((context + (dockerfile or "")).encode()).hexdigest()[:6]
            context_shorter = re.sub(r"https?://", "", context).replace(r".git", "")
            context_shorter = re.sub(r"[^a-zA-Z0-9_-]+", "-", context_shorter)[:32].lstrip("-") or "agent"
            image_name = f"{context_shorter}-{context_hash}:latest"
        else:
            # Strip any registry prefix — we always push to the platform registry
            image_name = tag.split("/")[-1]
            if ":" not in image_name:
                image_name += ":latest"
        image_name = image_name.lower()

        # Full image ref for cluster-internal use (pod specs)
        cluster_ref = f"{REGISTRY_INTERNAL}/{image_name}"
        # Local docker build tag
        build_tag = f"localhost/agentstack/{image_name}"

        # Build the image
        await run_command(
            ["docker", "build", context, *dockerfile_args, "-t", build_tag, "--load"],
            "Building agent image",
        )
        console.success(f"Built image: [bold]{build_tag}[/bold]")

        # Push to the in-cluster registry via NodePort (localhost:30500)
        from agentstack_cli.commands.platform import detect_export_import_paths, detect_vm_status, run_in_vm

        if (await detect_vm_status(vm_name)) != "running":
            console.error("Agent Stack platform is not running.")
            raise typer.Exit(1)

        host_path, guest_path = detect_export_import_paths()
        try:
            await run_command(
                ["docker", "image", "save", "-o", host_path, build_tag],
                f"Exporting image {build_tag} from Docker",
            )
            await run_in_vm(
                vm_name,
                [
                    "skopeo", "copy",
                    f"docker-archive:{guest_path}",
                    f"docker://localhost:{REGISTRY_NODEPORT}/{image_name}",
                    "--dest-tls-verify=false",
                ],
                "Pushing image to platform registry",
            )
        finally:
            await anyio.Path(host_path).unlink(missing_ok=True)

        console.success(
            f"Image pushed to platform registry.\n"
            f"Add it using: [green]agentstack add {cluster_ref}[/green]"
        )
