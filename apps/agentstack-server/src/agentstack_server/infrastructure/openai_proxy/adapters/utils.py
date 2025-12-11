# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import struct
from collections.abc import AsyncIterator, Iterable
from typing import Any

import openai.types

from agentstack_server.api.schema.openai import EmbeddingsRequest, MultiformatEmbedding
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.utils.utils import filter_dict


def float_list_to_base64(embedding: list[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(embedding)}f", *embedding)).decode("utf-8")


def iterate_in_threadpool[T](iterator: Iterable[T]) -> AsyncIterator[T]:
    from starlette.concurrency import iterate_in_threadpool

    return iterate_in_threadpool(iterator)


def convert_embedding_output(
    request: EmbeddingsRequest, result: openai.types.CreateEmbeddingResponse
) -> openai.types.CreateEmbeddingResponse:
    """
    Convert float embeddings to base64 if requested

    Despite the typing, OpenAI library does return str embeddings when base64 is requested
    However, some providers, like Ollama, silently don't support base64, so we have to convert
    """
    if request.encoding_format == "base64" and result.data and isinstance(result.data[0].embedding, list):
        result.data = [
            MultiformatEmbedding(object="embedding", index=emb.index, embedding=float_list_to_base64(emb.embedding))
            for emb in result.data
        ]
    result.model = request.model
    return result


def parse_openai_compatible_model(model_provider: ModelProvider, model: dict[str, Any]) -> Model:
    return Model.model_validate(
        filter_dict(
            {**model, "id": f"{model_provider.type}:{model['id']}", "provider": model_provider.model_provider_info}
        )
    )
