# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import contextvars
from collections import UserDict
from contextlib import contextmanager
from typing import Dict


# Store original environ and functions
_original_environ = os.environ
_original_getenv = os.getenv

# Context variable for environment overrides
_env_context: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar("env_context", default={})


def context_aware_getenv(key: str, default=None):
    """Context-aware replacement for os.getenv"""
    context_env = _env_context.get({})
    if key in context_env:
        return context_env[key]
    return _original_getenv(key, default)


class ContextAwareEnviron(UserDict):
    """Context-aware environment dictionary that checks context variables first"""

    def __init__(self, original_environ):
        # Don't call super().__init__() - we'll handle data ourselves
        self._original = original_environ

    @property
    def data(self):
        """Return merged environment (context overrides original)"""
        result = self._original.copy()
        context_env = _env_context.get({})
        result.update(context_env)
        return result

    def __getitem__(self, key):
        context_env = _env_context.get({})
        if key in context_env:
            return context_env[key]
        return self._original[key]

    def __setitem__(self, key, value):
        context_env = _env_context.get({}).copy()
        context_env[key] = value
        _env_context.set(context_env)

    def __delitem__(self, key):
        context_env = _env_context.get({}).copy()
        if key in context_env:
            del context_env[key]
            _env_context.set(context_env)
        elif key in self._original:
            del self._original[key]

    def __contains__(self, key):
        context_env = _env_context.get({})
        return key in context_env or key in self._original


def set_context_env(env_vars: Dict[str, str]):
    """Set environment variables for current context"""
    current_env = _env_context.get({}).copy()
    current_env.update(env_vars)
    _env_context.set(current_env)


@contextmanager
def with_local_env(env_vars: Dict[str, str]):
    """Context manager that sets up local environment context for this request"""
    # Store the current context
    old_context = _env_context.get({})

    # Set up new context with provided env vars
    set_context_env(env_vars)

    try:
        yield
    finally:
        # Restore the previous context
        _env_context.set(old_context)


def patch_os_environ():
    """Apply the context-aware patches to os.environ and os.getenv"""
    os.environ = ContextAwareEnviron(_original_environ)
    os.getenv = context_aware_getenv
