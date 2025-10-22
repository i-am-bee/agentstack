# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import difflib
import logging
from asyncio import TaskGroup
from collections import defaultdict
from contextlib import suppress
from datetime import timedelta
from uuid import UUID

from cachetools import TTLCache
from httpx import HTTPError
from kink import inject
from pydantic import HttpUrl

from beeai_server.domain.constants import MODEL_API_KEY_SECRET_NAME
from beeai_server.domain.models.model_provider import (
    Model,
    ModelCapability,
    ModelProvider,
    ModelProviderType,
    ModelWithScore,
)
from beeai_server.domain.repositories.env import EnvStoreEntity
from beeai_server.exceptions import EntityNotFoundError, ModelLoadFailedError
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ModelProviderService:
    _provider_models: TTLCache[UUID, list[Model]] = TTLCache(maxsize=100, ttl=timedelta(days=1).total_seconds())

    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

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
    ) -> ModelProvider:
        model_provider = ModelProvider(
            name=name,
            description=description,
            type=type,
            base_url=base_url,
            watsonx_project_id=watsonx_project_id,
            watsonx_space_id=watsonx_space_id,
        )
        # Check if models are available
        await self._get_provider_models(provider=model_provider, api_key=api_key, raise_error=True)

        async with self._uow() as uow:
            await uow.model_providers.create(model_provider=model_provider)
            await uow.env.update(
                parent_entity=EnvStoreEntity.MODEL_PROVIDER,
                parent_entity_id=model_provider.id,
                variables={MODEL_API_KEY_SECRET_NAME: api_key},
            )
            await uow.commit()
        return model_provider

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

    async def delete_provider(self, *, model_provider_id: UUID) -> None:
        """Delete a model provider and its environment variables."""
        async with self._uow() as uow:
            await uow.model_providers.delete(model_provider_id=model_provider_id)
            await uow.commit()
            self._provider_models.pop(model_provider_id, None)

    async def get_provider_api_key(self, *, model_provider_id: UUID) -> str:
        async with self._uow() as uow:
            # Check permissions
            await uow.model_providers.get(model_provider_id=model_provider_id)
            result = await uow.env.get(
                parent_entity=EnvStoreEntity.MODEL_PROVIDER,
                parent_entity_id=model_provider_id,
                key=MODEL_API_KEY_SECRET_NAME,
            )
            if not result:
                raise EntityNotFoundError("provider_variable", id=MODEL_API_KEY_SECRET_NAME)
            return result

    async def _get_provider_models(
        self, provider: ModelProvider, api_key: str, raise_error: bool = False
    ) -> list[Model]:
        try:
            if self._provider_models.get(provider.id) is None:
                self._provider_models[provider.id] = await provider.load_models(api_key=api_key)
            return self._provider_models[provider.id]
        except HTTPError as ex:
            if raise_error:
                raise ModelLoadFailedError(provider=provider, exception=ex) from ex
            logger.warning(f"Failed to load models for {provider.type} provider {provider.id}: {ex}")
        return []

    async def get_all_models(self) -> dict[str, tuple[ModelProvider, Model]]:
        async with self._uow() as uow, TaskGroup() as tg:
            providers = [provider async for provider in uow.model_providers.list()]
            all_env = await uow.env.get_all(
                parent_entity=EnvStoreEntity.MODEL_PROVIDER, parent_entity_ids=[p.id for p in providers]
            )
            for provider in providers:
                tg.create_task(
                    self._get_provider_models(
                        provider=provider, api_key=all_env[provider.id][MODEL_API_KEY_SECRET_NAME]
                    )
                )

        result = {}
        for provider in providers:
            for model in self._provider_models.get(provider.id, []):
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
