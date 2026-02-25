# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import typing
from typing import List, Literal

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions, ToolInputValidationError
from chat.tools.files.model import FileChatInfo
from pydantic import BaseModel, Field, create_model

from agentstack_sdk.platform import File


class FileReaderToolResult(BaseModel):
    file_contents: dict[str, str] = Field(
        ...,
        description="Content of the files that have been read, keyed by filename.",
    )


class FileReaderToolOutput(JSONToolOutput[FileReaderToolResult]):
    pass


class FileReadInputBase(BaseModel):
    """Base class for file read input to enable proper typing"""

    filenames: list[str]


class FileReaderTool(Tool[FileReadInputBase, ToolRunOptions, FileReaderToolOutput]):
    name: str = "file_reader"
    description: str = "Read content of one or more of the provided files."

    def __init__(self, files: list[FileChatInfo]) -> None:
        super().__init__()
        self.files = files
        self.files_dict = {file.display_filename: file for file in files}

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(namespace=["tool", "file_reader"], creator=self)

    @property
    def input_schema(self) -> type[FileReadInputBase]:
        if len(self.files):
            file_descriptions = "\n".join(file.description for file in self.files)

            description = f"Select one or more of the provided files:\n\n{file_descriptions}"
            # pyrefly: ignore [invalid-literal] -- it's a hack for JSON Schema generation
            literal = Literal[tuple(file.display_filename for file in self.files)]
        else:
            literal = Literal["__None__"]
            description = "There aren't any generated or attached file to read at the moment."

        return typing.cast(
            type[FileReadInputBase],
            create_model(
                "FileReadInput",
                filenames=(
                    List[literal],
                    Field(
                        ...,
                        description=description,
                    ),
                ),
            ),
        )

    async def _run(
        self, input: FileReadInputBase, options: ToolRunOptions | None, context: RunContext
    ) -> FileReaderToolOutput:
        if len(input.filenames) == 1 and input.filenames[0] == "__None__":
            return FileReaderToolOutput(
                result=FileReaderToolResult(file_contents={"__None__": "There are no files to read at the moment."})
            )

        file_contents = {}

        for filename in input.filenames:
            # validate that the filename is one of the provided files
            if filename not in self.files_dict:
                raise ToolInputValidationError(
                    f"Invalid file name: {filename}. Expected one of: {', '.join(self.files_dict.keys())}."
                )

            # get the FileInfo object for the requested file
            file_info = self.files_dict[filename]

            # pull the first (only) MessagePart from the async-generator
            async with File.load_content(file_info.file.id) as file:
                content = file.text
            if content is None:
                raise ValueError(f"File content is None for {filename}.")

            file_contents[filename] = content

        # wrap it in the expected output object
        return FileReaderToolOutput(result=FileReaderToolResult(file_contents=file_contents))
