import httpx
import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_files(subtests, setup_real_llm, api_client, acp_client):
    with subtests.test("upload file"):
        response = await api_client.post(
            "files", files={"file": ("test.txt", '{"hello": "world"}', "application/json")}
        )
        response.raise_for_status()
        file_id = response.json()["id"]

    with subtests.test("get file metadata"):
        response = await api_client.get(f"files/{file_id}")
        response.raise_for_status()
        assert response.json()["id"] == file_id

    with subtests.test("get file content"):
        response = await api_client.get(f"files/{file_id}/content")
        response.raise_for_status()
        assert response.json() == {"hello": "world"}
        assert response.headers["Content-Type"] == "application/json"

    with subtests.test("delete file"):
        response = await api_client.delete(f"files/{file_id}")
        response.raise_for_status()
        with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
            response = await api_client.get(f"files/{file_id}")
            response.raise_for_status()
