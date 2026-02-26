# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import difflib
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import timedelta
from typing import Final
from uuid import UUID

import openai.types.chat
from kink import inject
from pydantic import BaseModel, HttpUrl

from agentstack_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest
from agentstack_server.domain.constants import MODEL_API_KEY_SECRET_NAME
from agentstack_server.domain.models.model_provider import (
    Model,
    ModelCapability,
    ModelProvider,
    ModelProviderState,
    ModelProviderType,
    ModelWithScore,
)
from agentstack_server.domain.models.registry import ModelProviderRegistryLocation
from agentstack_server.domain.repositories.env import EnvStoreEntity
from agentstack_server.domain.repositories.openai_proxy import IOpenAIProxy
from agentstack_server.exceptions import EntityNotFoundError, InvalidProviderCallError, ModelLoadFailedError
from agentstack_server.infrastructure.cache.serializers import PydanticSerializer
from agentstack_server.service_layer.cache import ICache, ICacheFactory
from agentstack_server.service_layer.unit_of_work import IUnitOfWork, IUnitOfWorkFactory

logger = logging.getLogger(__name__)


class Models(BaseModel):
    models: list[Model]


@inject
class ModelProviderService:
    def __init__(self, uow: IUnitOfWorkFactory, openai_proxy: IOpenAIProxy, cache_factory: ICacheFactory):
        self._uow: Final[IUnitOfWorkFactory] = uow
        self._openai_proxy: Final[IOpenAIProxy] = openai_proxy
        self._cache: Final[ICache[Models]] = cache_factory.create(
            namespace="model_providers",
            serializer=PydanticSerializer(Models),
            ttl=timedelta(days=1),
        )

    async def create_provider(
        self,
        *,
        name: str | None,
        description: str | None,
        type: ModelProviderType,
        base_url: HttpUrl,
        watsonx_project_id: str | None = None,
        watsonx_space_id: str | None = None,
        api_key: str,
        registry: ModelProviderRegistryLocation | None = None,
    ) -> ModelProvider:
        model_provider = ModelProvider(
            name=name,
            description=description,
            type=type,
            base_url=base_url,
            watsonx_project_id=watsonx_project_id,
            watsonx_space_id=watsonx_space_id,
            registry=registry,
        )
        # Check if models are available
        models = await self._get_provider_models(provider=model_provider, api_key=api_key)

        async with self._uow() as uow:
            await uow.model_providers.create(model_provider=model_provider)
            await uow.env.update(
                parent_entity=EnvStoreEntity.MODEL_PROVIDER,
                parent_entity_id=model_provider.id,
                variables={MODEL_API_KEY_SECRET_NAME: api_key},
            )
            await uow.commit()
        await self._cache.set(str(model_provider.id), Models(models=models))
        return model_provider

    async def update_model_state_and_cache(self) -> None:
        async with self._uow() as uow:
            providers = [provider async for provider in uow.model_providers.list()]
            api_keys = await self._get_provider_api_keys(model_provider_ids=[p.id for p in providers], uow=uow)

        for model_provider, api_key in zip(providers, api_keys.values(), strict=True):
            try:
                models = await self._get_provider_models(provider=model_provider, api_key=api_key)
                await self._cache.set(str(model_provider.id), Models(models=models))
                updated_state = ModelProviderState.ONLINE
            except Exception as e:
                logger.error(f"Failed to update model cache for provider {model_provider.id}: {e}")
                updated_state = ModelProviderState.OFFLINE

            async with self._uow() as uow:
                await uow.model_providers.update_state(model_provider_id=model_provider.id, state=updated_state)
                await uow.commit()

    async def get_provider(self, *, model_provider_id: UUID) -> ModelProvider:
        """Get a model provider by ID."""
        async with self._uow() as uow:
            return await uow.model_providers.get(model_provider_id=model_provider_id)

    async def get_provider_by_model_id(self, *, model_id: str) -> ModelProvider:
        all_models = await self.get_all_models()
        if model_id not in all_models:
            raise EntityNotFoundError("model_provider", id=model_id)
        return all_models[model_id][0]

    async def list_providers(self) -> list[ModelProvider]:
        """List model providers, optionally filtered by capability."""
        async with self._uow() as uow:
            return [provider async for provider in uow.model_providers.list()]

    async def delete_provider(self, *, model_provider_id: UUID, allow_registry_update: bool = False) -> None:
        """Delete a model provider and its environment variables."""
        async with self._uow() as uow:
            if not allow_registry_update:
                provider = await uow.model_providers.get(model_provider_id=model_provider_id)
                if provider.registry:
                    raise InvalidProviderCallError("Cannot delete a provider managed by registry")

            await uow.model_providers.delete(model_provider_id=model_provider_id)
            await uow.commit()

        await self._cache.delete(str(model_provider_id))

    async def patch_provider(
        self,
        *,
        model_provider_id: UUID,
        name: str | None = None,
        base_url: HttpUrl | None = None,
        description: str | None = None,
        type: ModelProviderType | None = None,
        api_key: str | None = None,
        watsonx_project_id: str | None = None,
        watsonx_space_id: str | None = None,
        allow_registry_update: bool = False,
    ) -> ModelProvider:
        """Update a model provider."""

        async with self._uow() as uow:
            provider = await uow.model_providers.get(model_provider_id=model_provider_id)

            if provider.registry and not allow_registry_update:
                raise InvalidProviderCallError("Cannot update a provider managed by registry")

            old_api_key = await self._get_provider_api_keys(model_provider_ids=[model_provider_id], uow=uow)
            old_api_key = old_api_key[model_provider_id]

        updated_provider = provider.model_copy()
        updated_provider.name = name if name is not None else provider.name
        updated_provider.description = description if description is not None else provider.description
        updated_provider.type = type or updated_provider.type
        updated_provider.base_url = base_url or updated_provider.base_url
        updated_provider.watsonx_project_id = watsonx_project_id or updated_provider.watsonx_project_id
        updated_provider.watsonx_space_id = watsonx_space_id or updated_provider.watsonx_space_id

        updated_api_key = api_key or old_api_key

        should_update = provider != updated_provider or (updated_api_key != old_api_key)

        if should_update:
            # Check that provider works
            models = await self._get_provider_models(provider=updated_provider, api_key=updated_api_key)
            updated_provider.state = ModelProviderState.ONLINE

            async with self._uow() as uow:
                await uow.model_providers.update(model_provider=updated_provider)

                if updated_api_key != old_api_key:
                    await uow.env.update(
                        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
                        parent_entity_id=updated_provider.id,
                        variables={MODEL_API_KEY_SECRET_NAME: api_key},
                    )

                await uow.commit()

            await self._cache.set(str(model_provider_id), Models(models=models))

        return updated_provider

    async def _get_provider_api_keys(self, *, model_provider_ids: list[UUID], uow: IUnitOfWork) -> dict[UUID, str]:
        result = await uow.env.get_all(
            parent_entity=EnvStoreEntity.MODEL_PROVIDER,
            parent_entity_ids=model_provider_ids,
        )
        try:
            return {uuid: result[uuid][MODEL_API_KEY_SECRET_NAME] for uuid in model_provider_ids}
        except KeyError as e:
            raise EntityNotFoundError("provider_variable", id=MODEL_API_KEY_SECRET_NAME) from e

    async def get_provider_api_key(self, *, model_provider_id: UUID) -> str:
        async with self._uow() as uow:
            # Check permissions
            await uow.model_providers.get(model_provider_id=model_provider_id)
            api_keys = await self._get_provider_api_keys(model_provider_ids=[model_provider_id], uow=uow)
            return api_keys[model_provider_id]

    async def _get_provider_models(self, provider: ModelProvider, api_key: str) -> list[Model]:
        try:
            return await self._openai_proxy.list_models(provider=provider, api_key=api_key)
        except Exception as ex:
            raise ModelLoadFailedError(provider=provider, exception=ex) from ex

    async def get_all_models(self) -> dict[str, tuple[ModelProvider, Model]]:
        async with self._uow() as uow:
            providers = [
                provider async for provider in uow.model_providers.list() if provider.state == ModelProviderState.ONLINE
            ]

        cached_models = await self._cache.multi_get([str(p.id) for p in providers])
        result: dict[str, tuple[ModelProvider, Model]] = {}
        for provider, models in zip(providers, cached_models, strict=True):
            if not models:
                continue
            for model in models.models:
                result[model.id] = (provider, model)
        return result

    async def match_models(
        self, suggested_models: list[str] | None, capability: ModelCapability, score_cutoff: float = 0.4
    ) -> list[ModelWithScore]:
        """Match models based on suggestions and capability, fetching models and configuration from external sources."""
        all_models = await self.get_all_models()
        available_models = [
            m_id for m_id, (provider, model) in all_models.items() if capability in provider.capabilities
        ]

        configuration = None
        with suppress(EntityNotFoundError):
            async with self._uow() as uow:
                configuration = await uow.configuration.get_system_configuration()

        return self._match_models(
            available_models=available_models,
            suggested_models=suggested_models,
            capability=capability,
            score_cutoff=score_cutoff,
            default_llm_model=configuration.default_llm_model if configuration else None,
            default_embedding_model=configuration.default_embedding_model if configuration else None,
        )

    def _match_models(
        self,
        available_models: list[str],
        suggested_models: list[str] | None,
        capability: ModelCapability,
        score_cutoff: float,
        default_llm_model: str | None,
        default_embedding_model: str | None,
    ) -> list[ModelWithScore]:
        """Internal method to match models based on available models and configuration without external dependencies."""
        model_scores: dict[str, float] = defaultdict(float)

        # default models have score 0.5
        if default_llm_model and capability == ModelCapability.LLM:
            model_scores[default_llm_model] = 0.5
        if default_embedding_model and capability == ModelCapability.EMBEDDING:
            model_scores[default_embedding_model] = 0.5

        if suggested_models:
            for model in available_models:
                fuzzy_score = max(
                    (difflib.SequenceMatcher(None, model, suggested).ratio(), -idx)
                    for idx, suggested in enumerate(suggested_models)
                )[0]
                # (set score between 0.5, 1 if the original score is > fuzzy_score_cutoff)
                fuzzy_score = 0.5 + fuzzy_score / 2 if fuzzy_score > score_cutoff else 0.0
                model_scores[model] = max(model_scores[model], fuzzy_score)

        return [
            ModelWithScore(
                model_id=model_id,
                score=round(score, 2),
            )
            for model_id, score in sorted(model_scores.items(), key=lambda x: (-x[1], x[0]))
            if score >= 0.5  # global score cutoff
        ]

    async def create_chat_completion(self, request: ChatCompletionRequest) -> openai.types.chat.ChatCompletion:
        assert not request.stream
        provider = await self.get_provider_by_model_id(model_id=request.model)
        api_key = await self.get_provider_api_key(model_provider_id=provider.id)

        try:
            proxy = self._openai_proxy.get_chat_completion_proxy(provider=provider)
        except ValueError as e:
            raise InvalidProviderCallError("Provider does not support chat completions") from e

        return await proxy.create_chat_completion(request=request, api_key=api_key)

    async def create_chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        assert request.stream
        provider = await self.get_provider_by_model_id(model_id=request.model)
        api_key = await self.get_provider_api_key(model_provider_id=provider.id)

        try:
            proxy = self._openai_proxy.get_chat_completion_proxy(provider=provider)
        except ValueError as e:
            raise InvalidProviderCallError("Provider does not support chat completions") from e

        async for chunk in proxy.create_chat_completion_stream(request=request, api_key=api_key):
            yield chunk

    async def create_embedding(self, request: EmbeddingsRequest) -> openai.types.CreateEmbeddingResponse:
        provider = await self.get_provider_by_model_id(model_id=request.model)
        api_key = await self.get_provider_api_key(model_provider_id=provider.id)

        try:
            proxy = self._openai_proxy.get_embedding_proxy(provider=provider)
        except ValueError as e:
            raise InvalidProviderCallError("Provider does not support embeddings") from e

        return await proxy.create_embedding(request=request, api_key=api_key)
