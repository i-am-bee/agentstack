# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import List, Literal

from beeai_framework.emitter import Emitter
from beeai_framework.tools import (
    JSONToolOutput,
    Tool,
    ToolRunOptions,
)
from pydantic import BaseModel, Field, create_model

from chat.helpers.platform import read_file
from chat.tools.files.model import FileChatInfo
from chat.tools.files.utils import format_size


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


def create_file_reader_tool_class(files: list[FileChatInfo]) -> type[Tool]:
    """
    Dynamically creates a FileReaderTool class with a schema tailored to the provided files.
    
    This function generates a tool that can only read from the specific files that were provided,
    preventing small LLMs from hallucinating non-existent filenames. The input schema is 
    dynamically constructed using Pydantic's create_model to include only valid file options.
    
    Args:
        files: List of FileChatInfo objects representing available files for reading.
               Each file contains metadata like display_filename, content_type, and size.
    
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
            f"- `{file.display_filename}`[{file.origin_type.value}]: {file.content_type or 'unknown type'}, {format_size(file.file_size_bytes)}"
            for file in files
        )

        description = f"Select one or more of the provided files:\n\n{file_descriptions}"
        literal = Literal[tuple(file.display_filename for file in files)]
    else:
        literal = Literal["__None__"]
        description = "There aren't any generated or attached file to read at the moment."

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
        description: str = "Read content of one or more of the provided files."

        @property
        def input_schema(self):
            return FileReadInput

        def __init__(self) -> None:
            super().__init__()
            self.files = files
            self.files_dict = {file.display_filename: file for file in files}

        async def _run(
            self, input: FileReadInputBase, options, context
        ) -> FileReaderToolOutput:

            if len(input.filenames) == 1 and input.filenames[0] == "__None__":
                return FileReaderToolOutput(
                    result=FileReaderToolResult(
                        file_contents={"__None__": "There are no files to read at the moment."}
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
                file_info = self.files_dict[filename]

                # pull the first (only) MessagePart from the async-generator
                content = await read_file(file_info.url)
                if msg.content is None:
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
