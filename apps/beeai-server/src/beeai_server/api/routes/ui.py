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

import fastapi
import requests

from pydantic import BaseModel
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from beeai_server.configuration import UIFeatureFlags
from beeai_server.api.dependencies import ConfigurationDependency

router = fastapi.APIRouter()


@router.get("/config")
def get_ui_config(config: ConfigurationDependency) -> UIFeatureFlags:
    return config.feature_flags.ui


class SourceMetadata(BaseModel):
    title: str | None = None
    description: str | None = None
    favicon_url: str | None = None


# We plan to switch from Vite to Next.js for beeai-ui (https://github.com/i-am-bee/beeai-platform/pull/760), so then we can move this endpoint there.
@router.post("/source")
def get_source_metadata(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

    except requests.RequestException as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=f"Unable to fetch source url: {str(e)}"
        )

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        description_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        description = (
            description_tag["content"].strip() if description_tag and description_tag.has_attr("content") else None
        )

        favicon_url = extract_favicon_url(soup, url)

        return SourceMetadata(title=title, description=description, favicon_url=favicon_url)

    except Exception as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse source metadata: {str(e)}",
        )


def extract_favicon_url(soup: BeautifulSoup, url: str) -> str:
    favicon_tag = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
    favicon_path = favicon_tag["href"] if favicon_tag and favicon_tag.has_attr("href") else "favicon.ico"

    parsed_url = urlparse(url)
    origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    if favicon_path.startswith("http"):
        return favicon_path
    elif favicon_path.startswith("//"):
        return f"{parsed_url.scheme}:{favicon_path}"
    elif favicon_path.startswith("/"):
        return origin + favicon_path
    else:
        return f"{origin}/{favicon_path}"
