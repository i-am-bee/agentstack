# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import typing
from typing import Annotated

import fastapi
import openai.types.chat
from fastapi import Depends

from agentstack_server.api.constants import AGENTSTACK_PROXY_VERSION
from agentstack_server.api.dependencies import (
    ModelProviderServiceDependency,
    RequiresPermissions,
    UserRateLimiterDependency,
)
from agentstack_server.api.rate_limiter import RateLimit
from agentstack_server.api.schema.openai import (
    ChatCompletionRequest,
    EmbeddingsRequest,
    OpenAIPage,
)
from agentstack_server.api.utils import estimate_llm_cost, format_openai_error
from agentstack_server.domain.models.model_provider import Model
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()


@router.post("/chat/completions")
async def create_chat_completion(
    model_provider_service: ModelProviderServiceDependency,
    request: ChatCompletionRequest,
    user_rate_limiter: UserRateLimiterDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(llm={"*"}))],
):
    request_cost = estimate_llm_cost(request)
    await user_rate_limiter.hit(RateLimit.OPENAI_CHAT_COMPLETION_TOKENS, cost=request_cost)
    await user_rate_limiter.hit(RateLimit.OPENAI_CHAT_COMPLETION_REQUESTS)

    if request.stream:
        request.stream_options = request.stream_options or openai.types.chat.ChatCompletionStreamOptionsParam()
        request.stream_options["include_usage"] = True

        async def _stream():
            chunk = None
            total_estimated_cost = request_cost
            async for chunk in model_provider_service.create_chat_completion_stream(request=request):
                estimated_cost = estimate_llm_cost(chunk)
                total_estimated_cost += estimated_cost
                await user_rate_limiter.hit(RateLimit.OPENAI_CHAT_COMPLETION_TOKENS, cost=estimated_cost)
                yield json.dumps(chunk.model_dump(mode="json") | {"agentstack_proxy_version": AGENTSTACK_PROXY_VERSION})

            if chunk and chunk.usage and (total_cost := chunk.usage.total_tokens) and total_estimated_cost < total_cost:
                await user_rate_limiter.hit(
                    RateLimit.OPENAI_CHAT_COMPLETION_TOKENS, cost=total_cost - total_estimated_cost
                )
            # TODO: We might have overestimated the actual cost, can be resolved by clearing the limit
            # and hitting again with correct cost (careful about atomicity) or maybe using negative cost, but that is
            # not documented in the backend library. For simplicity, we ignore this case, because on average we have good estimates

        return streaming_response(_stream(), encode_exception=lambda e: json.dumps(format_openai_error(e)))

    response = await model_provider_service.create_chat_completion(request=request)
    cost = max(response.usage.total_tokens - request_cost, 0) if response.usage else estimate_llm_cost(response)
    await user_rate_limiter.hit(RateLimit.OPENAI_CHAT_COMPLETION_TOKENS, cost=cost)
    return response.model_dump(mode="json") | {"agentstack_proxy_version": AGENTSTACK_PROXY_VERSION}


@router.post("/embeddings")
async def create_embedding(
    request: EmbeddingsRequest,
    model_provider_service: ModelProviderServiceDependency,
    user_rate_limiter: UserRateLimiterDependency,
    _: typing.Annotated[AuthorizedUser, Depends(RequiresPermissions(embeddings={"*"}))],
):
    cost = len(request.input) if isinstance(request.input, list) else 1
    await user_rate_limiter.hit(RateLimit.OPENAI_EMBEDDING_ITEMS, cost=cost)
    result = await model_provider_service.create_embedding(request=request)
    return result.model_dump(mode="json") | {"agentstack_proxy_version": AGENTSTACK_PROXY_VERSION}


@router.get("/models")
async def list_models(
    model_provider_service: ModelProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"read"}))],
) -> OpenAIPage[Model]:
    all_models = await model_provider_service.get_all_models()
    return OpenAIPage(data=[model for _, model in all_models.values()])
