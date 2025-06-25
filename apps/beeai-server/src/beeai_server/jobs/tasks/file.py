# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from procrastinate import Blueprint


blueprint = Blueprint()


@blueprint.task(queue="text_extraction")
async def extract_text(file_id: UUID) -> str:
    # TODO: not implemented
    ...
