# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any, Final

from beeai_framework.context import RunContext

from beeai_sdk.platform import VectorStore
import httpx
from beeai_framework.emitter import Emitter
from beeai_framework.tools import Tool, ToolError, ToolOutput, ToolRunOptions
from pydantic import BaseModel, Field
from rag.helpers.vectore_store import EmbeddingFunction


class VectorSearchToolInput(BaseModel):
    """Input schema for vector search tool."""

    query: str = Field(description="The search query to find relevant documents.")


class VectorSearchToolResult(BaseModel):
    """Individual search result from vector store."""

    text: str = Field(description="The text content of the document chunk.")
    score: float = Field(description="Similarity score between 0.0 and 1.0.")
    metadata: dict[str, Any] = Field(description="Additional metadata for the document.")

    @property
    def title(self) -> str:
        """Get title from metadata or use truncated text."""
        if "filename" in self.metadata:
            return f"{self.metadata['filename']} (chunk {self.metadata.get('chunk_index', 0)})"
        elif "file_id" in self.metadata:
            return f"Document {self.metadata['file_id']} (chunk {self.metadata.get('chunk_index', 0)})"
        return self.text[:100] + "..." if len(self.text) > 100 else self.text

    @property
    def description(self) -> str:
        """Get description - use the text content."""
        return self.text

    @property
    def url(self) -> str:
        """Get URL from metadata or return empty string."""
        return self.metadata.get("url", "")


class VectorSearchToolOutput(ToolOutput):
    """Output for vector search tool."""

    def __init__(self, results: list[VectorSearchToolResult]) -> None:
        self.results = results
        self._platform_url: Final = os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")

    def get_text_content(self) -> str:
        """Get formatted text content of search results."""
        if not self.results:
            return "No relevant documents found."

        content = []
        for i, result in enumerate(self.results, 1):
            content.append(f"Result {i} (score: {result.score:.3f}):")
            content.append(f"Title: {result.title}")
            content.append(f"Content: {result.description}")
            if result.url:
                content.append(f"URL: {result.url}")
            content.append("")  # Empty line between results

        return "\n".join(content)

    def is_empty(self) -> bool:
        """Check if results are empty."""
        return len(self.results) == 0

    def sources(self) -> list[str]:
        """Get list of source URLs."""
        return [result.url for result in self.results if result.url]


class VectorSearchTool(Tool[VectorSearchToolInput, ToolRunOptions, VectorSearchToolOutput]):
    """
    Vector search tool for retrieving relevant documents from a vector database.

    This tool performs semantic search over previously embedded documents using
    vector similarity search to find the most relevant content for a given query.
    """

    name: str = "vector_search"
    description: str = (
        "Search for relevant information across multiple uploaded documents using semantic search. "
        "Use this tool for: research questions, content discovery across multiple files, "
        "and finding specific topics or concepts within documents. "
        "This tool finds the most relevant content based on meaning rather than exact keyword matching.\n\n"
        "# How to Create Effective Vector Search Queries:\n\n"
        "1. **Use Natural Language**: Write queries as you would ask a human expert\n"
        "   - Good: 'What are the benefits of renewable energy sources?'\n"
        "   - Poor: 'renewable energy benefits'\n\n"
        "2. **Be Specific and Descriptive**: Include context and specific terms\n"
        "   - Good: 'How does machine learning improve customer recommendation systems?'\n"
        "   - Poor: 'ML recommendations'\n\n"
        "3. **Ask Questions**: Frame queries as questions when looking for explanations\n"
        "   - Good: 'What factors contribute to employee satisfaction in remote work?'\n"
        "   - Poor: 'employee satisfaction factors'\n\n"
        "4. **Include Domain-Specific Terms**: Use technical vocabulary from the documents\n"
        "   - Good: 'API authentication methods and security best practices'\n"
        "   - Poor: 'security'\n\n"
        "5. **Search for Relationships**: Look for connections between concepts\n"
        "   - Good: 'Relationship between customer retention and pricing strategies'\n"
        "   - Poor: 'customer retention'\n\n"
        "6. **Use Multiple Searches**: Break complex questions into focused searches\n"
        "   - First: 'Cloud migration benefits and challenges'\n"
        "   - Then: 'Cost analysis of cloud vs on-premise infrastructure'\n"
        "   - Finally: 'Implementation timeline for cloud adoption'"
    )
    input_schema: type[VectorSearchToolInput] = VectorSearchToolInput

    def __init__(
        self,
        embedding_function: EmbeddingFunction,
        vector_store_id: str,
        limit: int = 5,
    ) -> None:
        super().__init__()
        self.embedding_function = embedding_function
        self.vector_store_id = vector_store_id
        self.limit = limit

    def _create_emitter(self) -> Emitter:
        """Create event emitter for tool events."""
        return Emitter.root().child(namespace=["tool", "vector_search"], creator=self)

    async def _run(
        self,
        input: VectorSearchToolInput,
        options: ToolRunOptions | None,
        context: RunContext,
    ) -> VectorSearchToolOutput:
        try:
            embed_response = await self.embedding_function(input=input.query)
            query_embedding = embed_response.data[0].embedding

            # Perform vector search
            search_results = await VectorStore.search(
                self.vector_store_id, query_vector=query_embedding, limit=self.limit
            )

            # Convert results to tool output format
            results = []
            for result in search_results:
                result_data = result.item
                score = result.score

                results.append(
                    VectorSearchToolResult(
                        text=result_data.text,
                        score=score,
                        metadata=result_data.metadata or {},
                    )
                )
            return VectorSearchToolOutput(results)
        except httpx.HTTPError as e:
            raise ToolError(f"HTTP error during vector search: {e}") from e
        except Exception as e:
            raise ToolError(f"Error performing vector search: {e}") from e

    def clone(self) -> "VectorSearchTool":
        """Create a copy of this tool."""
        return VectorSearchTool(
            embedding_function=self.embedding_function, vector_store_id=self.vector_store_id, limit=self.limit
        )
