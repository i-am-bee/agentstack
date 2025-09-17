# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import typing
from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions
from beeai_sdk.platform import File
from pydantic import BaseModel, Field


class FileInput(BaseModel):
    filename: str
    content_type: str
    content: str


class FileCreatorInput(BaseModel):
    files: list[FileInput]


class FileCreatorToolResult(BaseModel):
    files: list[File] = Field(
        ...,
        description="List of files that have been created.",
    )


class FileCreatorToolOutput(JSONToolOutput[FileCreatorToolResult]):
    pass


class FileCreatorTool(
    Tool[FileCreatorInput, ToolRunOptions, FileCreatorToolOutput]  # type: ignore
):
    """
    Creates a new file and writes the provided content into it.
    """

    name: str = "file_creator"
    description: str = "Create a new file with the specified content."
    input_schema: type[FileCreatorInput] = FileCreatorInput

    def __init__(
        self,
    ) -> None:
        super().__init__()

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "file_creator"],
            creator=self,
        )

    async def _run(self, input: FileCreatorInput, options, context) -> FileCreatorToolOutput:
        files: list[FileCreatorFile] = []
        for item in input.files:
            file = await File.create(
                filename=item.filename,
                content_type=item.content_type,
                content=item.content.encode(),
            )
            files.append(file)
        return FileCreatorToolOutput(result=FileCreatorToolResult(files=files))
