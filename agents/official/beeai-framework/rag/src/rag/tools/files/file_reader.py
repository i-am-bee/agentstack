# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import List, Literal

from beeai_framework.emitter import Emitter
from beeai_framework.tools import (
    JSONToolOutput,
    Tool,
    ToolRunOptions,
)
from beeai_sdk.platform import File
from pydantic import BaseModel, Field, create_model

from rag.tools.files.utils import File, format_size


class FileReaderToolResult(BaseModel):
    file_contents: dict[str, str] = Field(
        ...,
        description="Content of the files that have been read, keyed by filename.",
    )


class FileReaderToolOutput(JSONToolOutput[FileReaderToolResult]):
    pass


class FileReadInputBase(BaseModel):
    """Base class for file read input to enable proper typing"""

    filenames: List[str]


def create_file_reader_tool_class(files: list[File]) -> type[Tool]:
    """
    Dynamically creates a FileReaderTool class with a schema tailored to the provided files.

    This function generates a tool that can only read from the specific files that were provided,
    preventing small LLMs from hallucinating non-existent filenames. The input schema is
    dynamically constructed using Pydantic's create_model to include only valid file options.

    Args:
        files: List of File objects representing available files for reading.               

    Returns:
        A Tool class configured to read only from the provided files. The tool's input
        schema will restrict filename selection to only the files in the provided list.

    Behavior:
        - If files are provided: Creates a tool with Literal type constraints for filenames
        - If no files provided: Creates a tool that returns a "no files available" message
        - The tool validates all requested filenames against the provided file list
        - File contents are read asynchronously and returned as a dictionary
    """
    # 1. create a tailor-made Pydantic model

    if len(files):
        file_descriptions = "\n".join(
            f"- `{file.filename}`[{file.file_type}]: {format_size(file.file_size_bytes)}"
            for file in files
        )

        description = (
            f"Select one or more of the provided files:\n\n{file_descriptions}"
        )
        literal = Literal[tuple(file.filename for file in files)]
    else:
        literal = Literal["__None__"]
        description = (
            "There aren't any generated or attached file to read at the moment."
        )

    FileReadInput = create_model(
        "FileReadInput",
        filenames=(
            List[literal],
            Field(
                ...,
                description=description,
            ),
        ),
    )

    # 2. create a Tool subclass that *uses* that model
    class _FileReaderTool(Tool[FileReadInput, ToolRunOptions, FileReaderToolOutput]):
        """
        Reads and returns content of a file.
        """

        name: str = "file_reader"
        description: str = "Read complete content of specific files by name. Use this tool for: summarization tasks, accessing full file contents, and when working with individual files rather than searching across multiple documents."

        @property
        def input_schema(self):
            return FileReadInput

        def __init__(self) -> None:
            super().__init__()
            self.files = files
            self.files_dict = {file.filename: file for file in files}

        async def _run(
            self, input: FileReadInputBase, options, context
        ) -> FileReaderToolOutput:

            if len(input.filenames) == 1 and input.filenames[0] == "__None__":
                return FileReaderToolOutput(
                    result=FileReaderToolResult(
                        file_contents={
                            "__None__": "There are no files to read at the moment."
                        }
                    )
                )

            file_contents = {}

            for filename in input.filenames:
                # validate that the filename is one of the provided files
                if filename not in self.files_dict:
                    raise ValueError(
                        f"Invalid file name: {filename}. "
                        f"Expected one of: {', '.join(self.files_dict.keys())}."
                    )

                # get the FileInfo object for the requested file
                file = self.files_dict[filename]

                # pull the first (only) MessagePart from the async-generator
                async with file.load_text_content() as loaded_file:
                    content = loaded_file.text
                    content_type = loaded_file.content_type

                if content is None:
                    raise ValueError(f"File content is None for {filename}.")

                file_contents[filename] = content

            # wrap it in the expected output object
            return FileReaderToolOutput(
                result=FileReaderToolResult(file_contents=file_contents)
            )

        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "file_reader"],
                creator=self,
            )

    return _FileReaderTool  # type: ignore[return-value]
