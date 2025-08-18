# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from rag.helpers.platform import ApiClient


async def create_embedding(
    client: ApiClient, model: str = "dummy", input: list[str] = ["This is a test"]
):
    # FIXME: Raising 404
    # platform_url = os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")
    # async with AsyncOpenAI(
    #     api_key="dummy",
    #     base_url=platform_url,
    # ) as client:
    #     return await client.embeddings.create(model=model, input=input)

    response = await client.post(
        "llm/embeddings", json={"model": model, "input": input}
    )
    response_data = response.json()
    dimension = len(response_data["data"][0]["embedding"])

    return {"data": response_data["data"], "model": model, "dimension": dimension}
