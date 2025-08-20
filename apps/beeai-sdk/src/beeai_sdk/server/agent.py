# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import inspect
from asyncio import CancelledError
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from typing import NamedTuple, TypeAlias, cast

import janus
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue, QueueManager
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    SecurityScheme,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from beeai_sdk.a2a.extensions.ui.agent_detail import AgentDetail, AgentDetailExtensionSpec
from beeai_sdk.a2a.types import ArtifactChunk, Metadata, RunYield, RunYieldResume
from beeai_sdk.server.context import RunContext
from beeai_sdk.server.dependencies import extract_dependencies
from beeai_sdk.server.logging import logger
from beeai_sdk.server.utils import cancel_task

AgentFunction: TypeAlias = Callable[[], AsyncGenerator[RunYield, RunYieldResume]]
AgentFunctionFactory: TypeAlias = Callable[[TaskUpdater, RequestContext], AbstractAsyncContextManager[AgentFunction]]


class Agent(NamedTuple):
    card: AgentCard
    execute: AgentFunctionFactory


def agent(
    name: str | None = None,
    description: str | None = None,
    *,
    additional_interfaces: list[AgentInterface] | None = None,
    capabilities: AgentCapabilities | None = None,
    default_input_modes: list[str] | None = None,
    default_output_modes: list[str] | None = None,
    detail: AgentDetail | None = None,
    documentation_url: str | None = None,
    icon_url: str | None = None,
    preferred_transport: str | None = None,
    provider: AgentProvider | None = None,
    security: list[dict[str, list[str]]] | None = None,
    security_schemes: dict[str, SecurityScheme] | None = None,
    skills: list[AgentSkill] | None = None,
    supports_authenticated_extended_card: bool | None = None,
    version: str | None = None,
) -> Callable[[Callable], Agent]:
    """
    Create an Agent function.

    :param name: A human-readable name for the agent (inferred from the function name if not provided).
    :param description: A human-readable description of the agent, assisting users and other agents in understanding
        its purpose (inferred from the function docstring if not provided).
    :param additional_interfaces: A list of additional supported interfaces (transport and URL combinations).
        A client can use any of these to communicate with the agent.
    :param capabilities: A declaration of optional capabilities supported by the agent.
    :param default_input_modes: Default set of supported input MIME types for all skills, which can be overridden on
        a per-skill basis.
    :param default_output_modes: Default set of supported output MIME types for all skills, which can be overridden on
        a per-skill basis.
    :param detail: BeeAI SDK details extending the agent metadata
    :param documentation_url: An optional URL to the agent's documentation.
    :param extensions: BeeAI SDK extensions to apply to the agent.
    :param icon_url: An optional URL to an icon for the agent.
    :param preferred_transport: The transport protocol for the preferred endpoint. Defaults to 'JSONRPC' if not
        specified.
    :param provider: Information about the agent's service provider.
    :param security: A list of security requirement objects that apply to all agent interactions. Each object lists
        security schemes that can be used. Follows the OpenAPI 3.0 Security Requirement Object.
    :param security_schemes: A declaration of the security schemes available to authorize requests. The key is the
        scheme name. Follows the OpenAPI 3.0 Security Scheme Object.
    :param skills: The set of skills, or distinct capabilities, that the agent can perform.
    :param supports_authenticated_extended_card: If true, the agent can provide an extended agent card with additional
        details to authenticated users. Defaults to false.
    :param version: The agent's own version number. The format is defined by the provider.
    """

    capabilities = capabilities.model_copy(deep=True) if capabilities else AgentCapabilities(streaming=True)
    detail = detail or AgentDetail()  # pyright: ignore [reportCallIssue]

    def decorator(fn: Callable) -> Agent:
        signature = inspect.signature(fn)
        dependencies = extract_dependencies(signature)
        sdk_extensions = [dep.extension for dep in dependencies.values() if dep.extension is not None]

        resolved_name = name or fn.__name__
        resolved_description = description or fn.__doc__ or ""

        capabilities.extensions = [
            *(capabilities.extensions or []),
            *(AgentDetailExtensionSpec(detail).to_agent_card_extensions()),
            *(e_card for ext in sdk_extensions for e_card in ext.spec.to_agent_card_extensions()),
        ]

        card = AgentCard(
            additional_interfaces=additional_interfaces,
            capabilities=capabilities,
            default_input_modes=default_input_modes or ["text"],
            default_output_modes=default_output_modes or ["text"],
            description=resolved_description,
            documentation_url=documentation_url,
            icon_url=icon_url,
            name=resolved_name,
            preferred_transport=preferred_transport,
            provider=provider,
            security=security,
            security_schemes=security_schemes,
            skills=skills or [],
            supports_authenticated_extended_card=supports_authenticated_extended_card,
            url="http://localhost:10000",  # dummy url - will be replaced by server
            version=version or "1.0.0",
        )

        if inspect.isasyncgenfunction(fn):

            async def execute_fn(_ctx: RunContext, *args, **kwargs) -> None:
                try:
                    gen: AsyncGenerator[RunYield, RunYieldResume] = fn(*args, **kwargs)
                    value: RunYieldResume = None
                    while True:
                        value = await _ctx.yield_async(await gen.asend(value))
                except StopAsyncIteration:
                    pass
                except Exception as e:
                    await _ctx.yield_async(e)
                finally:
                    _ctx.shutdown()

        elif inspect.iscoroutinefunction(fn):

            async def execute_fn(_ctx: RunContext, *args, **kwargs) -> None:
                try:
                    await _ctx.yield_async(await fn(*args, **kwargs))
                except Exception as e:
                    await _ctx.yield_async(e)
                finally:
                    _ctx.shutdown()

        elif inspect.isgeneratorfunction(fn):

            def _execute_fn_sync(_ctx: RunContext, *args, **kwargs) -> None:
                try:
                    gen: Generator[RunYield, RunYieldResume] = fn(*args, **kwargs)
                    value = None
                    while True:
                        value = _ctx.yield_sync(gen.send(value))
                except StopIteration:
                    pass
                except Exception as e:
                    _ctx.yield_sync(e)
                finally:
                    _ctx.shutdown()

            async def execute_fn(_ctx: RunContext, *args, **kwargs) -> None:
                await asyncio.to_thread(_execute_fn_sync, _ctx, *args, **kwargs)

        else:

            def _execute_fn_sync(_ctx: RunContext, *args, **kwargs) -> None:
                try:
                    _ctx.yield_sync(fn(*args, **kwargs))
                except Exception as e:
                    _ctx.yield_sync(e)
                finally:
                    _ctx.shutdown()

            async def execute_fn(_ctx: RunContext, *args, **kwargs) -> None:
                await asyncio.to_thread(_execute_fn_sync, _ctx, *args, **kwargs)

        @asynccontextmanager
        async def agent_executor_lifespan(
            task_updater: TaskUpdater, request_context: RequestContext
        ) -> AsyncIterator[AgentFunction]:
            message = request_context.message
            assert message  # this is only executed in the context of SendMessage request
            # These are incorrectly typed in a2a
            assert request_context.task_id
            assert request_context.context_id
            context = RunContext(
                configuration=request_context.configuration,
                context_id=request_context.context_id,
                task_id=request_context.task_id,
                task_updater=task_updater,
                current_task=request_context.current_task,
                related_tasks=request_context.related_tasks,
                call_context=request_context.call_context,
            )

            # initialize dependencies
            async with AsyncExitStack() as stack:
                dependency_args = {}
                for pname, depends in dependencies.items():
                    # call dependencies with the first message and initialize their lifespan
                    dependency_args[pname] = await stack.enter_async_context(depends(message, context))

                async def agent_generator():
                    yield_queue = context._yield_queue
                    yield_resume_queue = context._yield_resume_queue

                    task = asyncio.create_task(execute_fn(context, **dependency_args))
                    try:
                        while not task.done() or yield_queue.async_q.qsize() > 0:
                            value = yield await yield_queue.async_q.get()
                            if isinstance(value, Exception):
                                raise value

                            if value:
                                # TODO: context.call_context should be updated here
                                # Unfortunately queue implementation does not support passing external types
                                # (only a2a.event_queue.Event is supported:
                                # Event = Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
                                for ext in sdk_extensions:
                                    ext.handle_incoming_message(value, context)

                            await yield_resume_queue.async_q.put(value)
                    except janus.AsyncQueueShutDown:
                        pass
                    except GeneratorExit:
                        return
                    finally:
                        await cancel_task(task)

                yield agent_generator

        return Agent(card=card, execute=agent_executor_lifespan)

    return decorator


class Executor(AgentExecutor):
    def __init__(self, execute_fn: AgentFunctionFactory, queue_manager: QueueManager) -> None:
        self._agent_executor_span = execute_fn
        self._queue_manager = queue_manager
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._cancel_queues: dict[str, EventQueue] = {}

    async def _watch_for_cancellation(self, task_id: str, task: asyncio.Task) -> None:
        cancel_queue = await self._queue_manager.create_or_tap(f"_cancel_{task_id}")
        self._cancel_queues[task_id] = cancel_queue

        try:
            await cancel_queue.dequeue_event()
            cancel_queue.task_done()
            task.cancel()
        finally:
            await self._queue_manager.close(f"_cancel_{task_id}")
            self._cancel_queues.pop(task_id)

    async def _run_agent_function(
        self,
        *,
        context: RequestContext,
        task_updater: TaskUpdater,
        resume_queue: EventQueue,
    ) -> None:
        current_task = asyncio.current_task()
        assert current_task
        cancellation_task = asyncio.create_task(self._watch_for_cancellation(task_updater.task_id, current_task))

        def with_context(message: Message | None = None) -> Message | None:
            if message is None:
                return None
            # Note: This check would require extra handling in agents just forwarding messages from other agents
            # Instead, we just silently replace it.
            # if message.task_id and message.task_id != task_updater.task_id:
            #     raise ValueError("Message must have the same task_id as the task")
            # if message.context_id and message.context_id != task_updater.context_id:
            #     raise ValueError("Message must have the same context_id as the task")
            return message.model_copy(
                deep=True, update={"context_id": task_updater.context_id, "task_id": task_updater.task_id}
            )

        async with self._agent_executor_span(task_updater, context) as execute_fn:
            agent_generator_fn = execute_fn()

            try:
                await task_updater.start_work()
                value: RunYieldResume = None
                opened_artifacts: set[str] = set()
                while True:
                    yielded_value = await agent_generator_fn.asend(value)
                    match yielded_value:
                        case str(text):
                            await task_updater.update_status(
                                TaskState.working,
                                message=task_updater.new_agent_message(parts=[Part(root=TextPart(text=text))]),
                            )
                        case Part(root=part) | (TextPart() | FilePart() | DataPart() as part):
                            await task_updater.update_status(
                                TaskState.working,
                                message=task_updater.new_agent_message(parts=[Part(root=part)]),
                            )
                        case FileWithBytes() | FileWithUri() as file:
                            await task_updater.update_status(
                                TaskState.working,
                                message=task_updater.new_agent_message(parts=[Part(root=FilePart(file=file))]),
                            )
                        case Message() as message:
                            await task_updater.update_status(TaskState.working, message=with_context(message))
                        case ArtifactChunk(
                            parts=parts, artifact_id=artifact_id, name=name, metadata=metadata, last_chunk=last_chunk
                        ):
                            await task_updater.add_artifact(
                                parts=cast(list[Part], parts),
                                artifact_id=artifact_id,
                                name=name,
                                metadata=metadata,
                                append=artifact_id in opened_artifacts,
                                last_chunk=last_chunk,
                            )
                            opened_artifacts.add(artifact_id)
                        case Artifact(parts=parts, artifact_id=artifact_id, name=name, metadata=metadata):
                            await task_updater.add_artifact(
                                parts=parts,
                                artifact_id=artifact_id,
                                name=name,
                                metadata=metadata,
                                last_chunk=True,
                                append=False,
                            )
                        case TaskStatus(state=TaskState.input_required, message=message, timestamp=timestamp):
                            await task_updater.requires_input(message=with_context(message), final=True)
                            value = cast(RunYieldResume, await resume_queue.dequeue_event())
                            resume_queue.task_done()
                            continue
                        case TaskStatus(state=TaskState.auth_required, message=message, timestamp=timestamp):
                            await task_updater.requires_auth(message=with_context(message), final=True)
                            value = cast(RunYieldResume, await resume_queue.dequeue_event())
                            resume_queue.task_done()
                            continue
                        case TaskStatus(state=state, message=message, timestamp=timestamp):
                            await task_updater.update_status(
                                state=state, message=with_context(message), timestamp=timestamp
                            )
                        case TaskStatusUpdateEvent(
                            status=TaskStatus(state=state, message=message, timestamp=timestamp), final=final
                        ):
                            await task_updater.update_status(
                                state=state, message=with_context(message), timestamp=timestamp, final=final
                            )
                        case TaskArtifactUpdateEvent(
                            artifact=Artifact(artifact_id=artifact_id, name=name, metadata=metadata, parts=parts),
                            append=append,
                            last_chunk=last_chunk,
                        ):
                            await task_updater.add_artifact(
                                parts=parts,
                                artifact_id=artifact_id,
                                name=name,
                                metadata=metadata,
                                append=append,
                                last_chunk=last_chunk,
                            )
                        case Metadata() as metadata:
                            await task_updater.update_status(
                                state=TaskState.working,
                                message=task_updater.new_agent_message(parts=[], metadata=metadata),
                            )
                        case dict() as data:
                            await task_updater.update_status(
                                state=TaskState.working,
                                message=task_updater.new_agent_message(parts=[Part(root=DataPart(data=data))]),
                            )
                        case Exception() as ex:
                            raise ex
                        case _:
                            raise ValueError(f"Invalid value yielded from agent: {type(yielded_value)}")
                    value = None
            except StopAsyncIteration:
                await task_updater.complete()
            except CancelledError:
                await task_updater.cancel()
            except Exception as ex:
                logger.error("Error when executing agent", exc_info=ex)
                await task_updater.failed(task_updater.new_agent_message(parts=[Part(root=TextPart(text=str(ex)))]))
            finally:
                await self._queue_manager.close(f"_event_{task_updater.task_id}")
                await self._queue_manager.close(f"_resume_{task_updater.task_id}")
                await cancel_task(cancellation_task)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        assert context.message  # this is only executed in the context of SendMessage request
        # These are incorrectly typed in a2a
        assert context.context_id
        assert context.task_id
        try:
            current_status = context.current_task and context.current_task.status.state
            if current_status == TaskState.working:
                raise RuntimeError("Cannot resume working task")
            if not context.task_id:
                raise RuntimeError("Task ID was not created")

            if not (resume_queue := await self._queue_manager.get(task_id=f"_resume_{context.task_id}")):
                resume_queue = await self._queue_manager.create_or_tap(task_id=f"_resume_{context.task_id}")

            if not (long_running_event_queue := await self._queue_manager.get(task_id=f"_event_{context.task_id}")):
                long_running_event_queue = await self._queue_manager.create_or_tap(task_id=f"_event_{context.task_id}")

            if current_status in {TaskState.input_required, TaskState.auth_required}:
                await resume_queue.enqueue_event(context.message)
            else:
                task_updater = TaskUpdater(long_running_event_queue, context.task_id, context.context_id)
                run_generator = self._run_agent_function(
                    context=context, task_updater=task_updater, resume_queue=resume_queue
                )
                self._running_tasks[context.task_id] = asyncio.create_task(run_generator)
                self._running_tasks[context.task_id].add_done_callback(
                    lambda _: self._running_tasks.pop(context.task_id)  # pyright: ignore [reportArgumentType]
                )

            while True:
                # Forward messages to local event queue
                event = await long_running_event_queue.dequeue_event()
                long_running_event_queue.task_done()
                await event_queue.enqueue_event(event)
                match event:
                    case TaskStatusUpdateEvent(final=True):
                        break
        except CancelledError:
            # Handles cancellation of this handler:
            # When a streaming request is canceled, this executor is canceled first meaning that "cancellation" event
            # passed from the agent's long_running_event_queue is not forwarded. Instead of shielding this function,
            # we report the cancellation explicitly
            local_updater = TaskUpdater(event_queue, task_id=context.task_id, context_id=context.context_id)
            await local_updater.cancel()
        except Exception as ex:
            logger.error("Error executing agent", exc_info=ex)
            local_updater = TaskUpdater(event_queue, task_id=context.task_id, context_id=context.context_id)
            await local_updater.failed(local_updater.new_agent_message(parts=[Part(root=TextPart(text=str(ex)))]))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("Task ID and context ID must be set to cancel a task")
        try:
            if context.current_task and (queue := self._cancel_queues.get(context.task_id)):
                await queue.enqueue_event(context.current_task)
        finally:
            await TaskUpdater(event_queue, task_id=context.task_id, context_id=context.context_id).cancel()
