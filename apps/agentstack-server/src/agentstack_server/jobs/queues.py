# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum


class Queues(StrEnum):
    # cron jobs
    CRON_CLEANUP = "cron:cleanup"
    CRON_MCP_PROVIDER = "cron:mcp_provider"
    CRON_PROVIDER = "cron:provider"
    CRON_CONNECTOR = "cron:connector"
    # tasks
    GENERATE_CONVERSATION_TITLE = "generate_conversation_title"
    TEXT_EXTRACTION = "text_extraction"
    TOOLKIT_DELETION = "toolkit_deletion"
    BUILD_PROVIDER = "build_provider"

    @staticmethod
    def all() -> set[str]:
        return {v.value for v in Queues.__members__.values()}  # pyright: ignore [reportAttributeAccessIssue]
