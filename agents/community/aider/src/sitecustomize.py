# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from aider.io import webbrowser

# disable all attempts to open browser
webbrowser.open = lambda *args, **kwargs: False
