# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from enum import StrEnum
from typing import Any

import httpx
from kink import di, inject
from pydantic import AnyUrl, BaseModel, ModelWrapValidatorHandler, RootModel, model_validator

logger = logging.getLogger(__name__)


class GithubVersionType(StrEnum):
    HEAD = "head"
    TAG = "tag"


class ResolvedGithubUrl(BaseModel):
    host: str = "github.com"
    org: str
    repo: str
    version: str
    version_type: GithubVersionType
    commit_hash: str
    path: str | None = None

    async def get_raw_url(self, path: str | None = None) -> AnyUrl:
        from beeai_server.configuration import Configuration

        configuration = di[Configuration]

        if not path and "." not in (self.path or ""):
            raise ValueError("Path is not specified or it is not a file")
        path = path or self.path
        if not path:
            raise ValueError("Path cannot be empty")
        # For github.com, use raw.githubusercontent.com, for enterprise use API
        if not (conf := configuration.github_registry.get(self.host)):
            if self.host == "github.com":
                return AnyUrl.build(
                    scheme="https",
                    host="raw.githubusercontent.com",
                    path=f"{self.org}/{self.repo}/{self.commit_hash}/{path.strip('/')}",
                )
            raise ValueError(f"GitHub token not configured for host: {self.host}")
        # For enterprise, we need to fetch the download_url from the API response
        token = conf.token.get_secret_value()
        api_host = f"{self.host}/api/v3"
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            resp = await client.get(
                (f"https://{api_host}/repos/{self.org}/{self.repo}/contents/{path.strip('/')}?ref={self.commit_hash}"),
                headers=headers,
            )
            resp.raise_for_status()
            content_data = resp.json()
            if "download_url" not in content_data:
                raise ValueError(f"File {path} not found or is not a file")
            return AnyUrl(content_data["download_url"])

    def __str__(self):
        path = f"#path={self.path}" if self.path else ""
        return f"git+https://{self.host}/{self.org}/{self.repo}@{self.commit_hash}{path}"


class GithubUrl(RootModel):
    root: str

    _org: str
    _repo: str
    _host: str = "github.com"
    _version: str | None = None
    _path: str | None = None

    @property
    def host(self) -> str:
        return self._host

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

    @model_validator(mode="wrap")
    @classmethod
    def _parse(cls, data: Any, handler: ModelWrapValidatorHandler):
        url: GithubUrl = handler(data)

        pattern = r"""
            ^
            (?:git\+)?                              # Optional git+ prefix
            https?://(?P<host>github(?:\.[^/]+)+)/  # GitHub host (github.com or github.enterprise.com)
            (?P<org>[^/]+)/                         # Organization
            (?P<repo>
                (?:                                 # Non-capturing group for repo name
                    (?!\.git(?:$|[@#]))             # Negative lookahead for .git at end or followed by @#
                    [^/@#]                          # Any char except /@#
                )+                                  # One or more of these chars
            )
            (?:\.git)?                              # Optional .git suffix
            (?:@(?P<version>[^#]+))?                # Optional version after @
            (?:\#path=(?P<path>.+))?                # Optional path after #path=
            $
        """
        match = re.match(pattern, url.root, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {data}")
        for name, value in match.groupdict().items():
            if value and not re.match(r"^[/a-zA-Z0-9._-]+$", value):
                raise ValueError(f"Invalid {name}: {value}")
            setattr(url, f"_{name}", value)
        url._path = url.path.strip("/") if url.path else None
        url.root = str(url)  # normalize url
        return url

    @inject
    async def _resolve_version_public(self) -> ResolvedGithubUrl:
        version = self._version or "HEAD"
        try:
            async with httpx.AsyncClient() as client:
                if not (version := self._version):
                    manifest_url = f"https://github.com/{self.org}/{self.repo}/blob/-/dummy"
                    resp = await client.head(manifest_url)
                    if not resp.headers.get("location", None):
                        raise ValueError(f"{self.path} not found in github repository.")
                    if match := re.search("/blob/([^/]*)", resp.headers["location"]):
                        version = match.group(1)

                assert version

                resp = await client.get(
                    f"https://github.com/{self._org}/{self._repo}.git/info/refs?service=git-upload-pack"
                )
                resp = resp.text.split("\n")
                [version_line] = [line for line in resp if line.endswith(f"/{version}")]
                [commit_hash, _ref_name] = version_line[4:].split()
                version_type = GithubVersionType.HEAD if "/refs/heads" in _ref_name else GithubVersionType.TAG
                return ResolvedGithubUrl(
                    host=self._host,
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

    async def _resolve_version_api(self, token: str) -> ResolvedGithubUrl:
        version = self._version
        api_host = f"{self._host}/api/v3"

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

                if not version:
                    # Get default branch
                    resp = await client.get(f"https://{api_host}/repos/{self._org}/{self._repo}", headers=headers)
                    resp.raise_for_status()
                    version = resp.json()["default_branch"]

                # Get commit hash for version
                resp = await client.get(
                    f"https://{api_host}/repos/{self._org}/{self._repo}/commits/{version}", headers=headers
                )
                resp.raise_for_status()
                commit_data = resp.json()
                commit_hash = commit_data["sha"]

                # Determine if it's a branch or tag
                version_type = GithubVersionType.HEAD
                try:
                    # Check if it's a tag
                    resp = await client.get(
                        f"https://{api_host}/repos/{self._org}/{self._repo}/git/refs/tags/{version}", headers=headers
                    )
                    if resp.status_code == 200:
                        version_type = GithubVersionType.TAG
                except Exception:
                    pass

                return ResolvedGithubUrl(
                    host=self._host,
                    org=self._org,
                    repo=self._repo,
                    version=version,
                    commit_hash=commit_hash,
                    path=self._path,
                    version_type=version_type,
                )
        except Exception as exc:
            raise ValueError(f"Failed to resolve github version for private repository: {exc!r}") from exc

    @inject
    async def resolve_version(self) -> ResolvedGithubUrl:
        from beeai_server.configuration import Configuration

        configuration = di[Configuration]

        if not (conf := configuration.github_registry.get(self._host)):
            if self._host == "github.com":
                return await self._resolve_version_public()
            raise ValueError(f"GitHub token not configured for host {self._host}")
        return await self._resolve_version_api(token=conf.token.get_secret_value())

    def __str__(self):
        version = f"@{self._version}" if self._version else ""
        path = f"#path={self.path}" if self.path else ""
        return f"git+https://{self._host}/{self.org}/{self.repo}{version}{path}"
