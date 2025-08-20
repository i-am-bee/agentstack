# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from gpt_researcher_agent.env_patch import patch_os_environ

# gpt researcher was never intended to be used in a server, we need to apply some ugly workarounds
# This needs to be done first before importing anything else
patch_os_environ()
