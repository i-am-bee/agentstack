# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from pydantic_settings import BaseSettings


class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"


class Configuration(BaseSettings):
    llm_model: str = "llama3.1"
    llm_api_base: str = "http://localhost:11434/v1"
    llm_api_key: str = "dummy"

    max_web_research_loops: int = 3
    search_api: SearchAPI = SearchAPI.DUCKDUCKGO
    fetch_full_page: bool = False
