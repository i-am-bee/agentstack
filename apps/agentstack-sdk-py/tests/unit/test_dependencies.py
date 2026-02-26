# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Annotated, TypedDict, Unpack

import pytest

from agentstack_sdk.a2a.extensions import CitationExtensionServer, CitationExtensionSpec
from agentstack_sdk.server.dependencies import extract_dependencies


class MyExtensions(TypedDict):
    a: Annotated[CitationExtensionServer, CitationExtensionSpec()]
    b: Annotated[CitationExtensionServer, CitationExtensionSpec()]
    c: Annotated[CitationExtensionServer, CitationExtensionSpec()]


class MyExtensionsComplex(TypedDict):
    b: Annotated[CitationExtensionServer, CitationExtensionSpec()]


@pytest.mark.unit
def test_extract_dependencies_simple() -> None:
    def agent(a: Annotated[CitationExtensionServer, CitationExtensionSpec()]) -> None:
        pass

    assert extract_dependencies(agent).keys() == {"a"}


@pytest.mark.unit
def test_extract_dependencies_extra_parameters() -> None:
    def agent(a: Annotated[CitationExtensionServer, CitationExtensionSpec()], b: bool) -> None:
        pass

    with pytest.raises(TypeError) as exc_info:
        extract_dependencies(agent)

    assert str(exc_info.value) == "The agent function contains extra parameters with unknown type annotation: {'b'}"


@pytest.mark.unit
def test_extract_dependencies_kwargs() -> None:
    def agent(**kwargs: Unpack[MyExtensions]) -> None:
        pass

    assert extract_dependencies(agent).keys() == {"a", "b", "c"}


@pytest.mark.unit
def test_extract_dependencies_complex() -> None:
    def agent(
        a: Annotated[CitationExtensionServer, CitationExtensionSpec()],
        **kwargs: Unpack[MyExtensionsComplex],
    ) -> None:
        pass

    assert extract_dependencies(agent).keys() == {"a", "b"}
