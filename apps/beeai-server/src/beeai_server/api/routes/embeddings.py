# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import fastapi
import ibm_watsonx_ai
import ibm_watsonx_ai.foundation_models.embeddings
import openai
import openai.types
import pydantic
from fastapi.concurrency import run_in_threadpool

from beeai_server.api.dependencies import EnvServiceDependency

router = fastapi.APIRouter()

BEEAI_PROXY_VERSION = 1


class EmbeddingsRequest(pydantic.BaseModel):
    """
    Corresponds to the arguments for OpenAI `client.embeddings.create(...)`.
    """

    model: str
    input: list[str] | str
    encoding_format: str | None = None


@router.post("/embeddings")
async def create_embedding(env_service: EnvServiceDependency, request: EmbeddingsRequest):
    env = await env_service.list_env()

    if pydantic.HttpUrl(env["EMBEDDING_API_BASE"]).host.endswith(".ml.cloud.ibm.com"):
        watsonx_response = await run_in_threadpool(
            ibm_watsonx_ai.foundation_models.embeddings.Embeddings(
                model_id=env["EMBEDDING_MODEL"],
                credentials=ibm_watsonx_ai.Credentials(url=env["EMBEDDING_API_BASE"], api_key=env["EMBEDDING_API_KEY"]),
                project_id=env.get("WATSONX_PROJECT_ID"),
                space_id=env.get("WATSONX_SPACE_ID"),
            ).generate,
            inputs=[request.input] if isinstance(request.input, str) else request.input,
        )
        return openai.types.CreateEmbeddingResponse(
            object="list",
            model=watsonx_response["model_id"],
            data=[
                openai.types.Embedding(
                    object="embedding",
                    index=i,
                    embedding=result["embedding"],
                )
                for i, result in enumerate(watsonx_response.get("results", []))
            ],
            usage=openai.types.create_embedding_response.Usage(
                prompt_tokens=watsonx_response.get("usage", {}).get("prompt_tokens", 0),
                total_tokens=watsonx_response.get("usage", {}).get("total_tokens", 0),
            ),
        ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
    else:
        return (
            await openai.AsyncOpenAI(
                api_key=env["EMBEDDING_API_KEY"],
                base_url=env["EMBEDDING_API_BASE"],
                default_headers=(
                    {"RITS_API_KEY": env["EMBEDDING_API_KEY"]}
                    if pydantic.HttpUrl(env["EMBEDDING_API_BASE"]).host.endswith(".rits.fmaas.res.ibm.com")
                    else {}
                ),
            ).embeddings.create(
                **(request.model_dump(mode="json", exclude_none=True) | {"model": env["EMBEDDING_MODEL"]})
            )
        ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
