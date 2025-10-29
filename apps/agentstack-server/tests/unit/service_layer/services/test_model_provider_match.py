# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

from agentstack_server.domain.models.model_provider import ModelCapability
from agentstack_server.service_layer.services.model_providers import ModelProviderService

pytestmark = pytest.mark.unit


class TestModelProviderMatchModels:
    """Test the _match_models functionality with scoring logic."""

    def test_default_model_gets_exactly_half_score(self):
        """Test that default models get exactly 0.5 score."""
        service = ModelProviderService(uow=None)  # We don't need UoW for internal method

        available_models = [
            "openai:gpt-4",
            "openai:gpt-3.5-turbo",
            "openai:text-embedding-ada-002",
            "anthropic:claude-3-5-sonnet",
        ]

        # Test LLM capability with default model
        result = service._match_models(
            available_models=available_models,
            suggested_models=None,
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model="openai:gpt-4",
            default_embedding_model=None,
        )

        # Should only return the default model with score 0.5
        assert len(result) == 1
        assert result[0].model_id == "openai:gpt-4"
        assert result[0].score == 0.5

        # Test embedding capability with default model
        result = service._match_models(
            available_models=available_models,
            suggested_models=None,
            capability=ModelCapability.EMBEDDING,
            score_cutoff=0.4,
            default_llm_model=None,
            default_embedding_model="openai:text-embedding-ada-002",
        )

        assert len(result) == 1
        assert result[0].model_id == "openai:text-embedding-ada-002"
        assert result[0].score == 0.5

    def test_exact_match_gets_score_of_one(self):
        """Test that exact matches get score of 1.0."""
        service = ModelProviderService(uow=None)

        available_models = ["openai:gpt-4", "openai:gpt-3.5-turbo", "anthropic:claude-3-5-sonnet"]

        # Test exact match
        result = service._match_models(
            available_models=available_models,
            suggested_models=["openai:gpt-4"],  # Exact match
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model=None,
            default_embedding_model=None,
        )

        # The exact match should get score 1.0
        gpt4_result = next((r for r in result if r.model_id == "openai:gpt-4"), None)
        assert gpt4_result is not None
        assert gpt4_result.score == 1.0

    def test_partial_match_gets_score_between_half_and_one(self):
        """Test that partial matches get scores between 0.5 and 1.0."""
        service = ModelProviderService(uow=None)

        available_models = [
            "openai:gpt-4",
            "openai:gpt-3.5-turbo",
        ]

        # Test partial match - "gpt-3.5" should partially match "openai:gpt-3.5-turbo"
        result = service._match_models(
            available_models=available_models,
            suggested_models=["gpt-3.5"],  # Partial match
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model=None,
            default_embedding_model=None,
        )

        gpt35_result = next((r for r in result if r.model_id == "openai:gpt-3.5-turbo"), None)
        assert gpt35_result is not None
        assert 0.5 < gpt35_result.score < 1.0

    def test_no_match_below_cutoff_gets_no_score(self):
        """Test that matches below cutoff don't appear in results."""
        service = ModelProviderService(uow=None)

        available_models = ["openai:gpt-4", "anthropic:claude-3-5-sonnet"]

        # Test with very poor match that should be below cutoff
        result = service._match_models(
            available_models=available_models,
            suggested_models=["xyz123nonexistent"],  # Should not match anything well
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model=None,
            default_embedding_model=None,
        )

        # Should return empty since no good matches and no default models
        assert len(result) == 0

    def test_default_model_gets_max_of_default_and_fuzzy_score(self):
        """Test that default models get max of default score (0.5) and fuzzy match score."""
        service = ModelProviderService(uow=None)

        available_models = ["openai:gpt-4", "openai:gpt-3.5-turbo"]

        # Set gpt-3.5-turbo as default but suggest gpt-4 exactly
        result = service._match_models(
            available_models=available_models,
            suggested_models=["openai:gpt-4"],  # Exact match should get 1.0
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model="openai:gpt-3.5-turbo",  # Default gets 0.5, but fuzzy match might be higher
            default_embedding_model=None,
        )

        # Both models should be in results
        assert len(result) == 2

        # Default model gets max of default score (0.5) and fuzzy score
        # Since "openai:gpt-4" partially matches "openai:gpt-3.5-turbo", it gets a fuzzy score > 0.5
        gpt35_result = next((r for r in result if r.model_id == "openai:gpt-3.5-turbo"), None)
        assert gpt35_result is not None
        assert gpt35_result.score >= 0.5  # Should be higher than default due to fuzzy match

        # Exact match should be 1.0 and should be first (higher score)
        gpt4_result = next((r for r in result if r.model_id == "openai:gpt-4"), None)
        assert gpt4_result is not None
        assert gpt4_result.score == 1.0

        # Results should be sorted by score (highest first)
        assert result[0].model_id == "openai:gpt-4"  # 1.0 score
        assert result[1].model_id == "openai:gpt-3.5-turbo"  # fuzzy score > 0.5

    def test_default_model_stays_exactly_half_when_no_fuzzy_match(self):
        """Test that default models stay at exactly 0.5 when there's no fuzzy matching improvement."""
        service = ModelProviderService(uow=None)

        available_models = [
            "openai:gpt-4",
            "anthropic:claude-3-5-sonnet",  # Very different, shouldn't fuzzy match well
        ]

        # Suggest something that won't improve the claude score
        result = service._match_models(
            available_models=available_models,
            suggested_models=["openai:gpt-4"],  # This shouldn't improve claude's score
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model="anthropic:claude-3-5-sonnet",  # Default should stay at 0.5
            default_embedding_model=None,
        )

        # Both models should be in results
        assert len(result) == 2

        # Default model should stay exactly at 0.5 (no fuzzy improvement)
        claude_result = next((r for r in result if r.model_id == "anthropic:claude-3-5-sonnet"), None)
        assert claude_result is not None
        assert claude_result.score == 0.5  # Should stay exactly at default

        # GPT-4 should get 1.0 for exact match
        gpt4_result = next((r for r in result if r.model_id == "openai:gpt-4"), None)
        assert gpt4_result is not None
        assert gpt4_result.score == 1.0

    def test_multiple_suggestions_best_match_wins(self):
        """Test that when multiple suggestions match, the best score is used."""
        service = ModelProviderService(uow=None)

        available_models = ["openai:gpt-4"]

        # Test with multiple suggestions of increasing quality
        result = service._match_models(
            available_models=available_models,
            suggested_models=["gpt", "gpt-4", "openai:gpt-4"],  # Progressive better matches
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model=None,
            default_embedding_model=None,
        )

        # Should get the best match (exact match = 1.0)
        assert len(result) == 1
        gpt4_result = result[0]
        assert gpt4_result.model_id == "openai:gpt-4"
        assert gpt4_result.score == 1.0

    def test_results_sorted_by_score_descending(self):
        """Test that results are sorted by score in descending order."""
        service = ModelProviderService(uow=None)

        available_models = ["openai:gpt-4", "openai:gpt-3.5-turbo", "anthropic:claude-3-5-sonnet"]

        # Create a scenario with different scores
        result = service._match_models(
            available_models=available_models,
            suggested_models=["openai:gpt-4", "claude"],  # Exact match + partial match
            capability=ModelCapability.LLM,
            score_cutoff=0.4,
            default_llm_model="openai:gpt-3.5-turbo",  # Default gets 0.5
            default_embedding_model=None,
        )

        # Results should be sorted by score descending
        assert len(result) > 1
        scores = [r.score for r in result]
        assert scores == sorted(scores, reverse=True)

        # First result should have highest score (exact match = 1.0)
        assert result[0].score > result[-1].score
        assert result[0].model_id == "openai:gpt-4"
        assert result[0].score == 1.0
