# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from pydantic import BaseModel, Field


class CreateVectorStoreRequest(BaseModel):
    """Request to create a new vector store."""

    name: str = Field(..., description="Name of the vector store")
    dimension: int = Field(..., description="Dimension of the vectors to be stored")
    model_id: str


class SearchRequest(BaseModel):
    """Request to search a vector store."""

    query_vector: list[float] = Field(description="Vector to search for")
    limit: int = Field(5, description="Maximum number of results to return", le=10)
