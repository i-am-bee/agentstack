# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import re
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import override

import aioboto3
import botocore.credentials
import openai
import openai.types.chat
from aws_bedrock_token_generator import provide_token

from agentstack_server.api.schema.openai import ChatCompletionRequest
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.infrastructure.openai_proxy.adapters.openai import OpenAIOpenAIProxyAdapter

logger = logging.getLogger(__name__)

# Cross-region inference profile prefixes or ARN patterns
_INFERENCE_PROFILE_RE = re.compile(r"^(us|eu|ap)\.|^arn:")


def _is_inference_profile(model_id: str) -> bool:
    """Return True if model_id is a cross-region inference profile (not a base model)."""
    return bool(_INFERENCE_PROFILE_RE.match(model_id))


def _parse_credentials(api_key: str) -> tuple[str, str, str | None, str | None]:
    """Parse 'access_key:secret_key[:session_token[:region]]' into components."""
    parts = api_key.split(":")
    access_key = parts[0]
    secret_key = parts[1]
    session_token = parts[2] if len(parts) >= 3 and parts[2] else None
    region = parts[3] if len(parts) >= 4 and parts[3] else None
    return access_key, secret_key, session_token, region


def _openai_messages_to_bedrock(
    messages: list,
) -> tuple[list[dict], list[dict]]:
    """Convert OpenAI-format messages to Bedrock Converse API format.

    Returns (system_prompts, messages).
    """
    system_prompts: list[dict] = []
    bedrock_messages: list[dict] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "system":
            if isinstance(content, str):
                system_prompts.append({"text": content})
            elif isinstance(content, list):
                for block in content:
                    if block.get("type") == "text":
                        system_prompts.append({"text": block.get("text", "")})
        else:
            if isinstance(content, str):
                bedrock_content = [{"text": content}]
            elif isinstance(content, list):
                bedrock_content = []
                for block in content:
                    if block.get("type") == "text":
                        bedrock_content.append({"text": block.get("text", "")})
            else:
                bedrock_content = [{"text": str(content)}]

            bedrock_messages.append({"role": role, "content": bedrock_content})

    return system_prompts, bedrock_messages


def _bedrock_stop_reason_to_openai(stop_reason: str) -> str:
    return {
        "end_turn": "stop",
        "max_tokens": "length",
        "stop_sequence": "stop",
        "tool_use": "tool_calls",
    }.get(stop_reason, "stop")


def _build_converse_kwargs(model_id: str, request: ChatCompletionRequest) -> dict:
    system_prompts, bedrock_messages = _openai_messages_to_bedrock(request.messages)  # type: ignore[arg-type]

    inference_config: dict = {}
    max_tokens = request.max_completion_tokens or request.max_tokens
    if max_tokens is not None:
        inference_config["maxTokens"] = max_tokens
    if request.temperature is not None:
        inference_config["temperature"] = request.temperature
    if request.top_p is not None:
        inference_config["topP"] = request.top_p
    if request.stop is not None:
        stop_seqs = [request.stop] if isinstance(request.stop, str) else list(request.stop)
        inference_config["stopSequences"] = stop_seqs

    kwargs: dict = {"modelId": model_id, "messages": bedrock_messages}
    if system_prompts:
        kwargs["system"] = system_prompts
    if inference_config:
        kwargs["inferenceConfig"] = inference_config
    return kwargs


class StaticCredentialsProvider(botocore.credentials.CredentialProvider):
    def __init__(self, access_key, secret_key, token=None):
        self._credentials = botocore.credentials.Credentials(access_key, secret_key, token)

    def load(self):
        return self._credentials


class BedrockOpenAIProxyAdapter(OpenAIOpenAIProxyAdapter):
    def __init__(self, provider: ModelProvider) -> None:
        super().__init__(provider)

    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        # Use the OpenAI-compatible /models endpoint (lists models available via /openai/v1)
        try:
            return await super().list_models(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to list Bedrock models via OpenAI-compatible endpoint: {e}")

        # Fallback: list via aioboto3 (foundation models + inference profiles)
        model_ids = []
        if ":" in api_key:
            try:
                access_key, secret_key, session_token, region = _parse_credentials(api_key)

                session = aioboto3.Session()
                async with session.client(
                    "bedrock",
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=session_token,
                ) as client:
                    fm_response = await client.list_foundation_models()
                    for fm in fm_response.get("modelSummaries", []):
                        if "ON_DEMAND" in fm.get("inferenceTypesSupported", []):
                            model_ids.append(fm["modelId"])

                    ip_response = await client.list_inference_profiles()
                    for ip in ip_response.get("inferenceProfileSummaries", []):
                        if ip.get("status") == "ACTIVE":
                            model_ids.append(ip["inferenceProfileId"])

            except Exception as e:
                logger.error(f"Failed to list Bedrock models via boto3: {e}")

        return [
            Model(
                id=f"{self.provider.type}:{m}",
                created=int(datetime.now().timestamp()),
                object="model",
                owned_by="aws",
                provider=self.provider.model_provider_info,
            )
            for m in model_ids
        ]

    @override
    def _get_client(self, api_key: str) -> openai.AsyncOpenAI:
        if ":" in api_key:
            try:
                access_key, secret_key, session_token, region = _parse_credentials(api_key)

                token = provide_token(
                    region=region,
                    aws_credentials_provider=StaticCredentialsProvider(
                        access_key=access_key, secret_key=secret_key, token=session_token
                    ),
                )
                return openai.AsyncOpenAI(api_key=token, base_url=str(self.provider.base_url))
            except Exception as e:
                logger.error(f"Failed to generate Bedrock token: {e}")

        return super()._get_client(api_key)

    @override
    async def create_chat_completion(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> openai.types.chat.ChatCompletion:
        raw_model_id = self.provider.get_raw_model_id(str(request.model))
        if _is_inference_profile(raw_model_id):
            return await self._converse(request=request, api_key=api_key, raw_model_id=raw_model_id)
        return await super().create_chat_completion(request=request, api_key=api_key)

    @override
    async def create_chat_completion_stream(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        raw_model_id = self.provider.get_raw_model_id(str(request.model))
        if _is_inference_profile(raw_model_id):
            async for chunk in self._converse_stream(request=request, api_key=api_key, raw_model_id=raw_model_id):
                yield chunk
        else:
            async for chunk in super().create_chat_completion_stream(request=request, api_key=api_key):
                yield chunk

    async def _converse(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
        raw_model_id: str,
    ) -> openai.types.chat.ChatCompletion:
        access_key, secret_key, session_token, region = _parse_credentials(api_key)
        kwargs = _build_converse_kwargs(raw_model_id, request)

        session = aioboto3.Session()
        async with session.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        ) as client:
            response = await client.converse(**kwargs)

        output_message = response["output"]["message"]
        content = "".join(block.get("text", "") for block in output_message.get("content", []))
        finish_reason = _bedrock_stop_reason_to_openai(response.get("stopReason", "end_turn"))
        usage = response.get("usage", {})

        return openai.types.chat.ChatCompletion.model_validate(
            {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": str(request.model),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": usage.get("inputTokens", 0),
                    "completion_tokens": usage.get("outputTokens", 0),
                    "total_tokens": usage.get("totalTokens", 0),
                },
            }
        )

    async def _converse_stream(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
        raw_model_id: str,
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        access_key, secret_key, session_token, region = _parse_credentials(api_key)
        kwargs = _build_converse_kwargs(raw_model_id, request)

        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(datetime.now().timestamp())
        model_id = str(request.model)

        session = aioboto3.Session()
        async with session.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        ) as client:
            response = await client.converse_stream(**kwargs)
            stream = response.get("stream")

            async for event in stream:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        yield openai.types.chat.ChatCompletionChunk.model_validate(
                            {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model_id,
                                "choices": [
                                    {"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}
                                ],
                            }
                        )
                elif "messageStop" in event:
                    stop_reason = _bedrock_stop_reason_to_openai(
                        event["messageStop"].get("stopReason", "end_turn")
                    )
                    yield openai.types.chat.ChatCompletionChunk.model_validate(
                        {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": stop_reason}],
                        }
                    )
