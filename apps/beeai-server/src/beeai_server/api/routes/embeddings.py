# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import base64
import struct
import typing

import fastapi
import ibm_watsonx_ai
import ibm_watsonx_ai.foundation_models.embeddings
import openai
import openai.types
import pydantic
from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from openai.types.create_embedding_response import CreateEmbeddingResponse

from beeai_server.api.dependencies import EnvServiceDependency, RequiresPermissions
from beeai_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()

BEEAI_PROXY_VERSION = 1


class EmbeddingsRequest(pydantic.BaseModel):
    """
    Corresponds to the arguments for OpenAI `client.embeddings.create(...)`.
    """

    model: str
    input: list[str] | str
    encoding_format: typing.Literal["float", "base64"] | None = None


class MultiformatEmbedding(openai.types.Embedding):
    embedding: str | list[float]


def _float_list_to_base64(embedding: list[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(embedding)}f", *embedding)).decode("utf-8")


@router.post("/embeddings")
async def create_embedding(
    env_service: EnvServiceDependency,
    request: EmbeddingsRequest,
    _: typing.Annotated[AuthorizedUser, Depends(RequiresPermissions(embeddings={"*"}))],
):
    env = await env_service.list_env()
    backend_url = pydantic.HttpUrl(env["EMBEDDING_API_BASE"])
    assert backend_url.host

    if backend_url.host.endswith("api.voyageai.com"):
        # Voyage does not support 'float' value: https://docs.voyageai.com/reference/embeddings-api
        request.encoding_format = None if request.encoding_format == "float" else request.encoding_format

    if backend_url.host.endswith(".ml.cloud.ibm.com"):
        watsonx_response = await run_in_threadpool(
            ibm_watsonx_ai.foundation_models.embeddings.Embeddings(
                model_id=env["EMBEDDING_MODEL"],
                credentials=ibm_watsonx_ai.Credentials(url=str(backend_url), api_key=env["EMBEDDING_API_KEY"]),
                project_id=env.get("WATSONX_PROJECT_ID"),
                space_id=env.get("WATSONX_SPACE_ID"),
            ).generate,
            inputs=[request.input] if isinstance(request.input, str) else request.input,
        )
        return openai.types.CreateEmbeddingResponse(
            object="list",
            model=watsonx_response["model_id"],
            data=[
                MultiformatEmbedding(
                    object="embedding",
                    index=i,
                    embedding=(
                        _float_list_to_base64(result["embedding"])
                        if request.encoding_format == "base64"
                        else typing.cast(list[float], result["embedding"])
                    ),
                )
                for i, result in enumerate(watsonx_response.get("results", []))
            ],
            usage=openai.types.create_embedding_response.Usage(
                prompt_tokens=watsonx_response.get("usage", {}).get("prompt_tokens", 0),
                total_tokens=watsonx_response.get("usage", {}).get("total_tokens", 0),
            ),
        ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
    else:
        result: CreateEmbeddingResponse = await openai.AsyncOpenAI(
            api_key=env["EMBEDDING_API_KEY"],
            base_url=str(backend_url),
            default_headers=(
                {"RITS_API_KEY": env["EMBEDDING_API_KEY"]}
                if backend_url.host.endswith(".rits.fmaas.res.ibm.com")
                else {}
            ),
        ).embeddings.create(**(request.model_dump(mode="json", exclude_none=True) | {"model": env["EMBEDDING_MODEL"]}))
        # Despite the typing, OpenAI library does return str embeddings when base64 is requested
        # However, some providers, like Ollama, silently don't support base64, so we have to convert
        if request.encoding_format == "base64" and isinstance(result.data[0].embedding, list):
            result.data = [
                MultiformatEmbedding(
                    object="embedding",
                    index=embedding.index,
                    embedding=_float_list_to_base64(embedding.embedding),
                )
                for embedding in result.data
            ]
        return result.model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
