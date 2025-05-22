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

import logging
import re
from enum import StrEnum
from typing import Any

import httpx
from pydantic import model_validator, AnyUrl, ModelWrapValidatorHandler, RootModel, BaseModel

logger = logging.getLogger(__name__)


class GithubVersionType(StrEnum):
    head = "head"
    tag = "tag"


class ResolvedGithubUrl(BaseModel):
    org: str
    repo: str
    version: str
    version_type: GithubVersionType
    commit_hash: str
    path: str | None = None

    def get_tgz_link(self) -> AnyUrl:
        version_type = "heads" if self._version_type == GithubVersionType.head else "tags"
        return AnyUrl.build(
            scheme="https",
            host="github.com",
            path=f"{self.org}/{self.repo}/archive/refs/{version_type}/{self.version}.tar.gz",
        )

    def get_raw_url(self, path: str | None = None) -> AnyUrl:
        if not path and "." not in (self.path or ""):
            raise ValueError("Path is not specified or it is not a file")
        path = path or self.path
        return AnyUrl.build(
            scheme="https",
            host="raw.githubusercontent.com",
            path=f"{self.org}/{self.repo}/{self.commit_hash}/{path.strip('/')}",
        )

    def __str__(self):
        path = f"#path={self.path}" if self.path else ""
        return f"git+https://github.com/{self.org}/{self.repo}@{self.version}{path}"


class GithubUrl(RootModel):
    root: str

    _org: str
    _repo: str
    _version: str | None = None
    _path: str | None = None

    @property
    def org(self) -> str:
        return self._org

    @property
    def repo(self) -> str:
        return self._repo

    @property
    def version(self) -> str | None:
        return self._version

    @property
    def path(self) -> str | None:
        return self._path

    @path.setter
    def path(self, value: str):
        self._path = value
        self.root = str(self)

    @property
    def commit_hash(self) -> str:
        if not self._resolved:
            raise ValueError("Version is not resolved")
        return self._commit_hash

    @model_validator(mode="wrap")
    @classmethod
    def _parse(cls, data: Any, handler: ModelWrapValidatorHandler):
        url: GithubUrl = handler(data)

        pattern = r"""
            ^
            (?:git\+)?                            # Optional git+ prefix
            https?://github\.com/                 # GitHub URL prefix
            (?P<org>[^/]+)/                       # Organization
            (?P<repo>
                (?:                               # Non-capturing group for repo name
                    (?!\.git(?:$|[@#]))           # Negative lookahead for .git at end or followed by @#
                    [^/@#]                        # Any char except /@#
                )+                                # One or more of these chars
            )
            (?:\.git)?                            # Optional .git suffix
            (?:@(?P<version>[^#]+))?              # Optional version after @
            (?:\#path=(?P<path>.+))?     # Optional path after #path=
            $
        """
        match = re.match(pattern, url.root, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {data}")
        for name, value in match.groupdict().items():
            setattr(url, f"_{name}", value)
        url._path = url.path.strip("/") if url.path else None
        url.root = str(url)  # normalize url
        return url

    async def resolve_version(self) -> ResolvedGithubUrl:
        try:
            async with httpx.AsyncClient() as client:
                if not (version := self._version):
                    manifest_url = f"https://github.com/{self.org}/{self.repo}/blob/-/dummy"
                    resp = await client.head(manifest_url)
                    if not resp.headers.get("location", None):
                        raise ValueError(f"{self.path} not found in github repository.")
                    version = re.search("/blob/([^/]*)", resp.headers["location"]).group(1)

                resp = await client.get(
                    f"https://github.com/{self._org}/{self._repo}.git/info/refs?service=git-upload-pack"
                )
                resp = resp.text.split("\n")
                [version_line] = [line for line in resp if line.endswith(f"/{version}")]
                [commit_hash, _ref_name] = version_line[4:].split()
                version_type = GithubVersionType.head if "/refs/heads" in _ref_name else GithubVersionType.tag
                return ResolvedGithubUrl(
                    org=self._org,
                    repo=self._repo,
                    version=version,
                    commit_hash=commit_hash,
                    path=self._path,
                    version_type=version_type,
                )
        except Exception as exc:
            raise ValueError(
                f"Failed to resolve github version, does the tag or branch {version} exist?: {exc!r}"
            ) from exc

    def __str__(self):
        version = f"@{self._version}" if self._version else ""
        path = f"#path={self.path}" if self.path else ""
        return f"git+https://github.com/{self.org}/{self.repo}{version}{path}"
