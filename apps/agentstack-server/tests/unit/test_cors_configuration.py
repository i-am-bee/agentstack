import pytest
from pydantic import ValidationError

from agentstack_server.configuration import CORSConfiguration


@pytest.mark.unit
def test_cors_default_configuration():
    """Test that default CORS configuration is disabled."""
    config = CORSConfiguration()
    assert config.enabled is False
    assert config.allow_credentials is False
    assert config.allow_origins == []
    assert config.allow_origin_regex is None


@pytest.mark.unit
def test_cors_validation_valid():
    """Test valid CORS configurations."""
    # Valid: origins provided
    CORSConfiguration(enabled=True, allow_origins=["http://example.com"], allow_origin_regex=None)

    # Valid: regex provided
    CORSConfiguration(enabled=True, allow_origins=[], allow_origin_regex=".*")

    # Valid: disabled, no origins
    CORSConfiguration(enabled=False, allow_origins=[], allow_origin_regex=None)


@pytest.mark.unit
def test_cors_empty_string_origin_regex():
    """Test that empty string for allow_origin_regex is treated as None."""
    config = CORSConfiguration(allow_origin_regex="")
    assert config.allow_origin_regex is None


@pytest.mark.unit
def test_cors_validation_wildcard_origins_with_credentials():
    """Test that wildcard origins are not allowed with credentials."""
    with pytest.raises(ValidationError, match=r"allow_origins cannot be '\*' when allow_credentials is True"):
        CORSConfiguration(enabled=True, allow_origins=["*"], allow_credentials=True)

    # Allowed if credentials is False
    CORSConfiguration(enabled=True, allow_origins=["*"], allow_credentials=False)
