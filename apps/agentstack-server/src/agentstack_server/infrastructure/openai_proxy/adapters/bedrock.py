# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import typing
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Final, override

import aioboto3
import openai.types.chat
from botocore.config import Config
from botocore.exceptions import ClientError

from agentstack_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest, MultiformatEmbedding
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.domain.repositories.openai_proxy import (
    IOpenAIChatCompletionProxyAdapter,
    IOpenAIEmbeddingProxyAdapter,
)
from agentstack_server.infrastructure.openai_proxy.adapters.utils import float_list_to_base64

BEDROCK_CONFIG = Config(
    read_timeout=1000,
    retries={"max_attempts": 3, "mode": "adaptive"},
)


class BedrockOpenAIProxyAdapter(IOpenAIChatCompletionProxyAdapter, IOpenAIEmbeddingProxyAdapter):
    def __init__(self, provider: ModelProvider) -> None:
        super().__init__()
        self.provider: Final[ModelProvider] = provider

    def _get_credentials(self, api_key: str) -> dict[str, str]:
        parts = api_key.split(":")
        # Format: access_key:secret_key:session_token:region
        # Or: access_key:secret_key::region
        # Or: :::region (IAM Role)
        if len(parts) < 4:
            raise ValueError("Invalid Bedrock API key format. Expected 4 parts separated by ':'")

        access_key, secret_key, session_token, region = parts[0], parts[1], parts[2], parts[3]

        credentials = {
            "region_name": region if region else None,
            "aws_access_key_id": access_key if access_key else None,
            "aws_secret_access_key": secret_key if secret_key else None,
            "aws_session_token": session_token if session_token else None,
        }
        return {k: v for k, v in credentials.items() if v is not None}

    def _get_bedrock_client(self, api_key: str):
        credentials = self._get_credentials(api_key)
        return aioboto3.Session().client("bedrock", config=BEDROCK_CONFIG, **typing.cast(typing.Any, credentials))

    def _get_bedrock_runtime_client(self, api_key: str):
        credentials = self._get_credentials(api_key)
        return aioboto3.Session().client(
            "bedrock-runtime", config=BEDROCK_CONFIG, **typing.cast(typing.Any, credentials)
        )

    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        async with self._get_bedrock_client(api_key) as client:
            response = await client.list_foundation_models()
            models = response.get("modelSummaries", [])
            return [
                Model(
                    id=f"{self.provider.type}:{model['modelId']}",
                    object="model",
                    owned_by=model.get("providerName", "unknown"),
                    created=int(datetime.now().timestamp()),  # Bedrock doesn't give creation date easily
                    provider=self.provider.model_provider_info,
                )
                for model in models
                if model.get("modelLifecycle", {}).get("status") == "ACTIVE"
            ]

    @override
    async def create_chat_completion(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> openai.types.chat.ChatCompletion:
        async with self._get_bedrock_runtime_client(api_key) as client:
            model_id = self.provider.get_raw_model_id(request.model)

            messages = []
            system_prompts = []

            # Request messages are typically [{"role": "user", "content": ...}, ...]
            # We need to ensure content is a string before passing to Bedrock
            for msg in request.messages:
                # msg is a dict from ChatCompletionRequest (pydantic model dumped or accessed)
                # If it's a dict:
                role = msg.get("role")
                content = msg.get("content")

                if role == "system":
                    if content:
                        system_prompts.append({"text": content})
                elif role in ("user", "assistant") and content:
                    messages.append({
                        "role": role,
                        "content": [{"text": content}]
                    })

            inference_config: dict[str, typing.Any] = {
                "maxTokens": request.max_tokens or request.max_completion_tokens or 2048,
                "temperature": request.temperature if request.temperature is not None else 0.7,
                "topP": request.top_p if request.top_p is not None else 1.0,
            }
            if request.stop:
                inference_config["stopSequences"] = [request.stop] if isinstance(request.stop, str) else request.stop

            try:
                response = await client.converse(
                    modelId=model_id,
                    messages=messages,
                    system=system_prompts,
                    inferenceConfig=inference_config,
                    # toolConfig=... # TODO: Implement tools support
                )
            except ClientError as e:
                # Map specific Bedrock errors if needed
                raise e

            output_message = response["output"]["message"]
            content = "".join([c["text"] for c in output_message["content"] if "text" in c])

            usage = response.get("usage", {})

            return openai.types.chat.ChatCompletion(
                id=f"chatcmpl-{datetime.now().timestamp()}",
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    openai.types.chat.chat_completion.Choice(
                        index=0,
                        message=openai.types.chat.ChatCompletionMessage(
                            role=output_message["role"],
                            content=content,
                        ),
                        finish_reason=response["stopReason"],
                    )
                ],
                usage=openai.types.CompletionUsage(
                    prompt_tokens=usage.get("inputTokens", 0),
                    completion_tokens=usage.get("outputTokens", 0),
                    total_tokens=usage.get("totalTokens", 0),
                ),
            )

    @override
    async def create_chat_completion_stream(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        async with self._get_bedrock_runtime_client(api_key) as client:
            model_id = self.provider.get_raw_model_id(request.model)

            messages = []
            system_prompts = []

            for msg in request.messages:
                role = msg.get("role")
                content = msg.get("content")

                if role == "system":
                    if content:
                        system_prompts.append({"text": content})
                elif role in ("user", "assistant") and content:
                    messages.append({
                        "role": role,
                        "content": [{"text": content}]
                    })

            inference_config: dict[str, typing.Any] = {
                "maxTokens": request.max_tokens or request.max_completion_tokens or 2048,
                "temperature": request.temperature if request.temperature is not None else 0.7,
                "topP": request.top_p if request.top_p is not None else 1.0,
            }
            if request.stop:
                inference_config["stopSequences"] = [request.stop] if isinstance(request.stop, str) else request.stop

            response = await client.converse_stream(
                modelId=model_id,
                messages=messages,
                system=system_prompts,
                inferenceConfig=inference_config,
            )

            stream = response.get("stream")
            if stream:
                async for event in stream:
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]
                        delta_text = delta["delta"].get("text", "")
                        yield openai.types.chat.ChatCompletionChunk(
                            id=f"chatcmpl-{datetime.now().timestamp()}",
                            object="chat.completion.chunk",
                            created=int(datetime.now().timestamp()),
                            model=request.model,
                            choices=[
                                openai.types.chat.chat_completion_chunk.Choice(
                                    index=delta["contentBlockIndex"],
                                    delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(
                                        content=delta_text,
                                        role="assistant" if delta["contentBlockIndex"] == 0 else None
                                    ),
                                    finish_reason=None,
                                )
                            ],
                        )
                    elif "messageStop" in event:
                        yield openai.types.chat.ChatCompletionChunk(
                            id=f"chatcmpl-{datetime.now().timestamp()}",
                            object="chat.completion.chunk",
                            created=int(datetime.now().timestamp()),
                            model=request.model,
                            choices=[
                                openai.types.chat.chat_completion_chunk.Choice(
                                    index=0,
                                    delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(),
                                    finish_reason=event["messageStop"]["stopReason"],
                                )
                            ],
                        )

    @override
    async def create_embedding(
        self,
        *,
        request: EmbeddingsRequest,
        api_key: str,
    ) -> openai.types.CreateEmbeddingResponse:
        model_id = self.provider.get_raw_model_id(request.model)

        async with self._get_bedrock_runtime_client(api_key) as client:
            inputs = [request.input] if isinstance(request.input, str) else request.input
            embeddings = []
            total_tokens = 0

            for i, text in enumerate(inputs):
                embedding_vector = None
                token_count = 0

                if "titan-embed" in model_id:
                    body = {"inputText": text}
                    response = await client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body)
                    )
                    response_body = json.loads(await response["body"].read())
                    embedding_vector = response_body.get("embedding")
                    token_count = response_body.get("inputTextTokenCount", 0)
                elif "cohere.embed" in model_id:
                    body = {"texts": [text], "input_type": "search_document"}
                    response = await client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body)
                    )
                    response_body = json.loads(await response["body"].read())
                    # Cohere returns 'embeddings' list
                    if response_body.get("embeddings"):
                        embedding_vector = response_body["embeddings"][0]
                    token_count = 0
                else:
                    # Fallback assuming Titan-like interface
                    body = {"inputText": text}
                    response = await client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body)
                    )
                    response_body = json.loads(await response["body"].read())
                    embedding_vector = response_body.get("embedding")
                    token_count = response_body.get("inputTextTokenCount", 0)

                if embedding_vector:
                    embeddings.append(
                         MultiformatEmbedding(
                            object="embedding",
                            index=i,
                            embedding=(
                                float_list_to_base64(embedding_vector)
                                if request.encoding_format == "base64"
                                else typing.cast(list[float], embedding_vector)
                            ),
                        )
                    )
                    total_tokens += token_count

            return openai.types.CreateEmbeddingResponse(
                object="list",
                model=request.model,
                data=embeddings,
                usage=openai.types.create_embedding_response.Usage(
                    prompt_tokens=total_tokens,
                    total_tokens=total_tokens,
                ),
            )
