# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from langchain_text_splitters import MarkdownTextSplitter


def chunk_markdown(markdown_text: str) -> list[str]:
    return MarkdownTextSplitter().split_text(markdown_text)
