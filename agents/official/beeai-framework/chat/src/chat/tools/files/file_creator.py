# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions
from pydantic import BaseModel, Field

from chat.helpers.platform import get_file_url, upload_file
from chat.tools.files.model import FileChatInfo, OriginType


class FileInput(BaseModel):
    filename: str
    content_type: str
    content: str


class FileCreatorInput(BaseModel):
    files: list[FileInput]


class FileCreatorToolResult(BaseModel):
    files: list[FileChatInfo] = Field(
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

    name: str = "FileCreator"
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

    async def _run(
        self, input: FileCreatorInput, options, context
    ) -> FileCreatorToolOutput:
        files = []
        for item in input.files:
            result = await upload_file(
                filename=item.filename,
                content_type=item.content_type,
                content=item.content.encode(),
            )
            files.append(
                FileChatInfo(
                    id=result.id,
                    url=get_file_url(result.id),
                    content_type=item.content_type,
                    display_filename=item.filename,
                    filename=item.filename,
                    file_size_bytes=result.file_size_bytes,
                    origin_type=OriginType.GENERATED,
                )
            )
        return FileCreatorToolOutput(result=FileCreatorToolResult(files=files))
