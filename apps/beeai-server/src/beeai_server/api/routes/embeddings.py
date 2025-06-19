# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import traceback
from typing import Dict, List

from beeai_framework.adapters.openai.backend.embedding import OpenAIEmbeddingModel
from beeai_framework.adapters.watsonx.backend.embedding import WatsonxEmbeddingModel
from beeai_framework.backend.types import EmbeddingModelOutput
import fastapi
from pydantic import BaseModel

from beeai_server.api.dependencies import EnvServiceDependency


router = fastapi.APIRouter()


class EmbeddingsRequest(BaseModel):
    model: str
    input: List[str] | str


class EmbeddingsDataItem(BaseModel):
    object: str = "embedding"
    index: int
    embedding: List[float]


class EmbeddingsResponse(BaseModel):
    object: str = "list"
    system_fingerprint: str = "beeai-embeddings-gateway"
    model: str
    usage: Dict[str, int] = {
        "prompt_tokens": int,
        "total_tokens": int,
        "completion_tokens": int,
    }
    data: List[EmbeddingsDataItem]


@router.post("")
async def create_embeddings(
    env_service: EnvServiceDependency,
    request: EmbeddingsRequest,
):
    env = await env_service.list_env()

    is_rits = re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm.com/.*$", env["LLM_API_BASE"])
    is_watsonx = re.match(r"^https://[a-z0-9.-]+\.ml\.cloud\.ibm\.com.*?$", env["LLM_API_BASE"])

    print(env)
    embeddings = (
        WatsonxEmbeddingModel(
            model_id=env["EMBEDDING_MODEL"],
            api_key=env["LLM_API_KEY"],
            base_url=env["LLM_API_BASE"],
            project_id=env.get("WATSONX_PROJECT_ID"),
            space_id=env.get("WATSONX_SPACE_ID"),
        )
        if is_watsonx
        else OpenAIEmbeddingModel(
            env["EMBEDDING_MODEL"],
            api_key=env["LLM_API_KEY"],
            base_url=env["LLM_API_BASE"],
            extra_headers={"RITS_API_KEY": env["LLM_API_KEY"]} if is_rits else {},
        )
    )

    output = None
    try:
        output: EmbeddingModelOutput = await embeddings.create(
            values=(request.input if isinstance(request.input, list) else [request.input]),
        )
    except Exception as e:
        traceback.print_exc()
        print(e)

    return EmbeddingsResponse(
        model=request.model,
        data=[EmbeddingsDataItem(index=i, embedding=embedding) for i, embedding in enumerate(output.embeddings)],
        usage={
            "prompt_tokens": output.usage.prompt_tokens,
            "completion_tokens": output.usage.completion_tokens,
            "total_tokens": output.usage.total_tokens,
        },
    )
