# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import re

from agentstack_sdk.a2a.extensions import Citation


def extract_citations(text: str) -> tuple[list[Citation], str]:
    """
    Extract citations from markdown-style links and return cleaned text.

    This function parses text containing markdown-style citations in the format
    [citation_text](url) and extracts them into Citation objects while cleaning
    the original text to contain only the citation content.

    Args:
        text (str): Input text containing markdown-style citations

    Returns:
        tuple[list[Citation], str]: A tuple containing:
            - List of Citation objects with metadata
            - Cleaned text with citation links replaced by content only

    Example:
        >>> text = "According to [recent studies](https://example.com/study) and [research papers](https://academic.org/paper), AI is advancing rapidly."
        >>> citations, clean_text = extract_citations(text)
        >>> print(clean_text)
        "According to recent studies and research papers, AI is advancing rapidly."
        >>> print(len(citations))
        2
        >>> print(citations[0].url)
        "https://example.com/study"
        >>> print(citations[0].title)
        "Study"
        >>> print(citations[0].description)
        "recent studies"
    """
    citations, offset = [], 0
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    for match in re.finditer(pattern, text):
        content, url = match.groups()
        start = match.start() - offset

        citations.append(
            Citation(
                url=url,
                title=url.split("/")[-1].replace("-", " ").title() or content[:50],
                description=content[:100] + ("..." if len(content) > 100 else ""),
                start_index=start,
                end_index=start + len(content),
            )
        )
        offset += len(match.group(0)) - len(content)

    return citations, re.sub(pattern, r"\1", text)
