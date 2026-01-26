# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from uuid import UUID

import httpx
from kink import inject

from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.domain.models.user_feedback import UserFeedback
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class UserFeedbackService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow

        self._phoenix_client = (
            httpx.AsyncClient(
                base_url=str(configuration.telemetry.phoenix_url),
                headers={"authorization": f"Bearer {configuration.telemetry.phoenix_api_key.get_secret_value()}"}
                if configuration.telemetry.phoenix_api_key
                else None,
            )
            if configuration.telemetry.phoenix_url
            else None
        )

    async def __aenter__(self):
        if self._phoenix_client:
            await self._phoenix_client.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        if self._phoenix_client:
            await self._phoenix_client.__aexit__(exc_type, exc, tb)

    async def create_user_feedback(
        self,
        *,
        provider_id: UUID,
        rating: int,
        comment: str | None = None,
        comment_tags: list[str] | None = None,
        message: str,
        task_id: UUID,
        context_id: UUID,
        user: User,
    ):
        async with self._uow() as uow:
            try:
                task = await uow.a2a_requests.get_task(task_id=str(task_id), user_id=user.id)
                trace_id = task.trace_id
            except EntityNotFoundError:
                trace_id = None

            user_feedback = UserFeedback(
                provider_id=provider_id,
                rating=rating,
                comment=comment,
                comment_tags=comment_tags,
                message=message,
                task_id=task_id,
                context_id=context_id,
                created_by=user.id,
                trace_id=trace_id,
            )
            await uow.user_feedback.create(user_feedback=user_feedback)
            await uow.commit()
            asyncio.create_task(self._try_send_to_phoenix(user_feedback=user_feedback))  # noqa: RUF006
            return user_feedback

    async def list_user_feedback(
        self,
        *,
        user: User,
        provider_id: UUID | None = None,
        limit: int = 50,
        after_cursor: UUID | None = None,
    ) -> tuple[list[UserFeedback], int, bool]:
        if user.role not in (UserRole.ADMIN, UserRole.DEVELOPER):
            raise ValueError("Listing feedback is only allowed for admins and developers")

        provider_created_by = user.id if user.role == UserRole.DEVELOPER else None

        async with self._uow() as uow:
            feedback_list, total, has_more = await uow.user_feedback.list(
                provider_created_by=provider_created_by,
                provider_id=provider_id,
                limit=limit,
                after_cursor=after_cursor,
            )
            return feedback_list, total, has_more

    async def _try_send_to_phoenix(self, *, user_feedback: UserFeedback) -> None:
        if self._phoenix_client is None or user_feedback.trace_id is None:
            return

        try:
            response = await self._phoenix_client.post(
                "/graphql",
                json={
                    "query": "query GetTraceByOtelId($traceId: String!) { getTraceByOtelId(traceId: $traceId) { spans(rootSpansOnly: true, orphanSpanAsRootSpan: true) { edges { node { spanId }}} }}",
                    "variables": {"traceId": user_feedback.trace_id},
                },
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise ValueError(data["errors"])
            elif "data" not in data or "getTraceByOtelId" not in data["data"]:
                raise ValueError("Invalid response")

            span_id = data["data"]["getTraceByOtelId"]["spans"]["edges"][0]["node"]["spanId"]
            if span_id is None:
                raise ValueError("No span found")

            response = await self._phoenix_client.post(
                "/v1/span_annotations",
                json={
                    "data": [
                        {
                            "name": "Feedback",
                            "annotator_kind": "HUMAN",
                            "span_id": span_id,
                            "result": {
                                "label": None,
                                "score": user_feedback.rating,
                                "explanation": user_feedback.comment,
                            },
                        }
                    ]
                },
            )
            response.raise_for_status()
        except Exception:
            logger.warning("Failed to send user feedback to Phoenix", exc_info=True)
