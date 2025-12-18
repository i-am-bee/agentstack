# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import inspect
import typing
from asyncio import CancelledError
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager, suppress
from datetime import datetime, timedelta
from typing import Any, NamedTuple, TypeAlias, TypeVar, cast

import janus
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue, QueueManager
from a2a.server.tasks import TaskManager, TaskStore, TaskUpdater
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
from typing_extensions import override

from agentstack_sdk.a2a.extensions.ui.agent_detail import AgentDetail, AgentDetailExtensionSpec
from agentstack_sdk.a2a.extensions.ui.error import (
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
    get_error_extension_context,
)
from agentstack_sdk.a2a.types import ArtifactChunk, Metadata, RunYield, RunYieldResume
from agentstack_sdk.server.constants import _IMPLICIT_DEPENDENCY_PREFIX
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.dependencies import Depends, extract_dependencies
from agentstack_sdk.server.store.context_store import ContextStore
from agentstack_sdk.server.utils import cancel_task
from agentstack_sdk.util.logging import logger

AgentFunction: TypeAlias = Callable[[], AsyncGenerator[RunYield, RunYieldResume]]
AgentFunctionFactory: TypeAlias = Callable[[RequestContext, ContextStore], AbstractAsyncContextManager[AgentFunction]]

OriginalFnType = TypeVar("OriginalFnType", bound=Callable[..., Any])  # pyright: ignore[reportExplicitAny]


class AgentExecuteFn(typing.Protocol):
    async def __call__(self, _ctx: RunContext, **kwargs: Any) -> None: ...


class Agent(NamedTuple):
    card: AgentCard
    dependencies: dict[str, Depends]
    execute_fn: AgentExecuteFn


AgentFactory: TypeAlias = Callable[[Callable[[dict[str, Depends]], None]], Agent]


def agent(
    name: str | None = None,
    description: str | None = None,
    *,
    url: str = "http://invalid",  # Default will be replaced by the server
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
) -> Callable[[OriginalFnType], AgentFactory]:
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
    :param detail: Agent Stack SDK details extending the agent metadata
    :param documentation_url: An optional URL to the agent's documentation.
    :param extensions: Agent Stack SDK extensions to apply to the agent.
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

    def decorator(fn: OriginalFnType) -> AgentFactory:
        def agent_factory(modify_dependencies: Callable[[dict[str, Depends]], None]):
            signature = inspect.signature(fn)
            dependencies = extract_dependencies(signature)
            modify_dependencies(dependencies)

            sdk_extensions = [dep.extension for dep in dependencies.values() if dep.extension is not None]

            resolved_name = name or fn.__name__
            resolved_description = description or fn.__doc__ or ""

            # Check if user has provided an ErrorExtensionServer, if not add default
            has_error_extension = any(isinstance(ext, ErrorExtensionServer) for ext in sdk_extensions)
            error_extension_spec = ErrorExtensionSpec(ErrorExtensionParams()) if not has_error_extension else None

            capabilities.extensions = [
                *(capabilities.extensions or []),
                *(AgentDetailExtensionSpec(detail).to_agent_card_extensions()),
                *(error_extension_spec.to_agent_card_extensions() if error_extension_spec else []),
                *(e_card for ext in sdk_extensions for e_card in ext.spec.to_agent_card_extensions()),
            ]

            card = AgentCard(
                url=url,
                preferred_transport=preferred_transport,
                additional_interfaces=additional_interfaces,
                capabilities=capabilities,
                default_input_modes=default_input_modes or ["text"],
                default_output_modes=default_output_modes or ["text"],
                description=resolved_description,
                documentation_url=documentation_url,
                icon_url=icon_url,
                name=resolved_name,
                provider=provider,
                security=security,
                security_schemes=security_schemes,
                skills=skills or [],
                supports_authenticated_extended_card=supports_authenticated_extended_card,
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

            return Agent(card=card, dependencies=dependencies, execute_fn=execute_fn)

        return agent_factory

    return decorator


class AgentRun:
    def __init__(self, agent: Agent, context_store: ContextStore, on_finish: Callable[[], None] | None = None) -> None:
        self._agent: Agent = agent
        self._task: asyncio.Task[None] | None = None
        self.last_invocation: datetime = datetime.now()
        self.resume_queue: asyncio.Queue[RunYieldResume] = asyncio.Queue()
        self._run_context: RunContext | None = None
        self._task_updater: TaskUpdater | None = None
        self._context_store: ContextStore = context_store
        self._lock: asyncio.Lock = asyncio.Lock()
        self._on_finish: Callable[[], None] | None = on_finish
        self._working: bool = False

    @property
    def run_context(self) -> RunContext:
        if not self._run_context:
            raise RuntimeError("Accessing run context for run that has not been started")
        return self._run_context

    @property
    def task_updater(self) -> TaskUpdater:
        if not self._task_updater:
            raise RuntimeError("Accessing task updater for run that has not been started")
        return self._task_updater

    @property
    def done(self) -> bool:
        return self._task is not None and self._task.done()

    def _handle_finish(self) -> None:
        if self._on_finish:
            self._on_finish()

    async def start(self, request_context: RequestContext, event_queue: EventQueue):
        # These are incorrectly typed in a2a
        async with self._lock:
            if self._working or self.done:
                raise RuntimeError("Attempting to start a run that is already executing or done")
            task_id, context_id, message = request_context.task_id, request_context.context_id, request_context.message
            assert task_id and context_id and message
            self._run_context = RunContext(
                configuration=request_context.configuration,
                context_id=context_id,
                task_id=task_id,
                current_task=request_context.current_task,
                related_tasks=request_context.related_tasks,
            )
            self._task_updater = TaskUpdater(event_queue, task_id, context_id)
            if not request_context.current_task:
                await self._task_updater.submit()
            await self._task_updater.start_work()
            self._working = True
            self._task = asyncio.create_task(self._run_agent_function(initial_message=message))

    async def resume(self, request_context: RequestContext, event_queue: EventQueue):
        # These are incorrectly typed in a2a
        async with self._lock:
            if self._working or self.done:
                raise RuntimeError("Attempting to resume a run that is already executing or done")
            task_id, context_id, message = request_context.task_id, request_context.context_id, request_context.message
            assert task_id and context_id and message
            self._task_updater = TaskUpdater(event_queue, task_id, context_id)

            for dependency in self._agent.dependencies.values():
                if dependency.extension:
                    dependency.extension.handle_incoming_message(message, self.run_context)

            self._working = True
            await self.resume_queue.put(message)

    async def cancel(self, request_context: RequestContext, event_queue: EventQueue):
        if not self._task:
            raise RuntimeError("Cannot cancel run that has not been started")

        async with self._lock:
            try:
                assert request_context.task_id
                assert request_context.context_id
                self._task_updater = TaskUpdater(event_queue, request_context.task_id, request_context.context_id)
                await self._task_updater.cancel()
            finally:
                await cancel_task(self._task)

    @asynccontextmanager
    async def _dependencies_lifespan(self, message: Message) -> AsyncIterator[dict[str, Depends]]:
        async with AsyncExitStack() as stack:
            dependency_args: dict[str, Depends] = {}
            initialize_deps_exceptions: list[Exception] = []
            for pname, depends in self._agent.dependencies.items():
                # call dependencies with the first message and initialize their lifespan
                try:
                    dependency_args[pname] = await stack.enter_async_context(
                        depends(message, self.run_context, dependency_args)
                    )
                except Exception as e:
                    initialize_deps_exceptions.append(e)

            if initialize_deps_exceptions:
                raise (
                    ExceptionGroup("Failed to initialize dependencies", initialize_deps_exceptions)
                    if len(initialize_deps_exceptions) > 1
                    else initialize_deps_exceptions[0]
                )

            self.run_context._store = await self._context_store.create(  # pyright: ignore[reportPrivateUsage]
                context_id=self.run_context.context_id,
                initialized_dependencies=list(dependency_args.values()),
            )

            yield {k: v for k, v in dependency_args.items() if not k.startswith(_IMPLICIT_DEPENDENCY_PREFIX)}

    def _with_context(self, message: Message | None = None) -> Message | None:
        if message is None:
            return None
        # Note: This check would require extra handling in agents just forwarding messages from other agents
        # Instead, we just silently replace it.
        # if message.task_id and message.task_id != task_updater.task_id:
        #     raise ValueError("Message must have the same task_id as the task")
        # if message.context_id and message.context_id != task_updater.context_id:
        #     raise ValueError("Message must have the same context_id as the task")
        return message.model_copy(
            deep=True, update={"context_id": self.task_updater.context_id, "task_id": self.task_updater.task_id}
        )

    async def _run_agent_function(self, initial_message: Message) -> None:
        yield_queue = self.run_context._yield_queue  # pyright: ignore[reportPrivateUsage]
        yield_resume_queue = self.run_context._yield_resume_queue  # pyright: ignore[reportPrivateUsage]

        try:
            async with self._dependencies_lifespan(initial_message) as dependency_args:
                task = asyncio.create_task(self._agent.execute_fn(self.run_context, **dependency_args))
                try:
                    resume_value: RunYieldResume = None
                    opened_artifacts: set[str] = set()
                    while not task.done() or yield_queue.async_q.qsize() > 0:
                        yielded_value = await yield_queue.async_q.get()

                        self.last_invocation = datetime.now()

                        match yielded_value:
                            case str(text):
                                await self.task_updater.update_status(
                                    TaskState.working,
                                    message=self.task_updater.new_agent_message(parts=[Part(root=TextPart(text=text))]),
                                )
                            case Part(root=part) | (TextPart() | FilePart() | DataPart() as part):
                                await self.task_updater.update_status(
                                    TaskState.working,
                                    message=self.task_updater.new_agent_message(parts=[Part(root=part)]),
                                )
                            case FileWithBytes() | FileWithUri() as file:
                                await self.task_updater.update_status(
                                    TaskState.working,
                                    message=self.task_updater.new_agent_message(parts=[Part(root=FilePart(file=file))]),
                                )
                            case Message() as message:
                                await self.task_updater.update_status(
                                    TaskState.working, message=self._with_context(message)
                                )
                            case ArtifactChunk(
                                parts=parts,
                                artifact_id=artifact_id,
                                name=name,
                                metadata=metadata,
                                last_chunk=last_chunk,
                            ):
                                await self.task_updater.add_artifact(
                                    parts=cast(list[Part], parts),
                                    artifact_id=artifact_id,
                                    name=name,
                                    metadata=metadata,
                                    append=artifact_id in opened_artifacts,
                                    last_chunk=last_chunk,
                                )
                                opened_artifacts.add(artifact_id)
                            case Artifact(parts=parts, artifact_id=artifact_id, name=name, metadata=metadata):
                                await self.task_updater.add_artifact(
                                    parts=parts,
                                    artifact_id=artifact_id,
                                    name=name,
                                    metadata=metadata,
                                    last_chunk=True,
                                    append=False,
                                )
                            case TaskStatus(
                                state=(TaskState.auth_required | TaskState.input_required) as state,
                                message=message,
                                timestamp=timestamp,
                            ):
                                await self.task_updater.update_status(
                                    state=state, message=self._with_context(message), final=True, timestamp=timestamp
                                )
                                self._working = False
                                resume_value = await self.resume_queue.get()
                                self.resume_queue.task_done()
                            case TaskStatus(state=state, message=message, timestamp=timestamp):
                                await self.task_updater.update_status(
                                    state=state, message=self._with_context(message), timestamp=timestamp
                                )
                            case TaskStatusUpdateEvent(
                                status=TaskStatus(state=state, message=message, timestamp=timestamp),
                                final=final,
                                metadata=metadata,
                            ):
                                await self.task_updater.update_status(
                                    state=state,
                                    message=self._with_context(message),
                                    timestamp=timestamp,
                                    final=final,
                                    metadata=metadata,
                                )
                            case TaskArtifactUpdateEvent(
                                artifact=Artifact(artifact_id=artifact_id, name=name, metadata=metadata, parts=parts),
                                append=append,
                                last_chunk=last_chunk,
                            ):
                                await self.task_updater.add_artifact(
                                    parts=parts,
                                    artifact_id=artifact_id,
                                    name=name,
                                    metadata=metadata,
                                    append=append,
                                    last_chunk=last_chunk,
                                )
                            case Metadata() as metadata:
                                await self.task_updater.update_status(
                                    state=TaskState.working,
                                    message=self.task_updater.new_agent_message(parts=[], metadata=metadata),
                                )
                            case dict() as data:
                                await self.task_updater.update_status(
                                    state=TaskState.working,
                                    message=self.task_updater.new_agent_message(parts=[Part(root=DataPart(data=data))]),
                                )
                            case Exception() as ex:
                                raise ex
                            case _:
                                raise ValueError(f"Invalid value yielded from agent: {type(yielded_value)}")

                        await yield_resume_queue.async_q.put(resume_value)

                    await self.task_updater.complete()

                except (janus.AsyncQueueShutDown, GeneratorExit):
                    await self.task_updater.complete()
                except Exception as ex:
                    logger.error("Error when executing agent", exc_info=ex)
                    await self.task_updater.failed(get_error_extension_context().server.message(ex))
                    await cancel_task(task)
        except Exception as ex:
            logger.error("Error when executing agent", exc_info=ex)
            await self.task_updater.failed(get_error_extension_context().server.message(ex))
        finally:
            self._working = False
            with suppress(Exception):
                self._handle_finish()


class Executor(AgentExecutor):
    def __init__(
        self,
        agent: Agent,
        queue_manager: QueueManager,
        context_store: ContextStore,
        task_timeout: timedelta,
        task_store: TaskStore,
    ) -> None:
        self._agent: Agent = agent
        self._running_tasks: dict[str, AgentRun] = {}
        self._scheduled_cleanups: dict[str, asyncio.Task[None]] = {}
        self._context_store: ContextStore = context_store
        self._task_timeout: timedelta = task_timeout
        self._task_store: TaskStore = task_store

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # this is only executed in the context of SendMessage request
        message, task_id, context_id = context.message, context.task_id, context.context_id
        assert message and task_id and context_id
        agent_run: AgentRun | None = None
        try:
            if not context.current_task:
                agent_run = AgentRun(self._agent, self._context_store, lambda: self._handle_finish(task_id))
                self._running_tasks[task_id] = agent_run
                await self._schedule_run_cleanup(request_context=context)
                await agent_run.start(request_context=context, event_queue=event_queue)
            elif agent_run := self._running_tasks.get(task_id):
                await agent_run.resume(request_context=context, event_queue=event_queue)
            else:
                raise self._run_not_found_error(task_id)

            # will run until complete or next input/auth required task state
            tapped_queue = event_queue.tap()
            while True:
                match await tapped_queue.dequeue_event():
                    case TaskStatusUpdateEvent(final=True):
                        break

        except CancelledError:
            if agent_run:
                await agent_run.cancel(request_context=context, event_queue=event_queue)
        except Exception as ex:
            logger.error("Unhandled error when executing agent:", exc_info=ex)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("Task ID and context ID must be set to cancel a task")
        if not (run := self._running_tasks.get(context.task_id)):
            raise self._run_not_found_error(context.task_id)
        await run.cancel(context, event_queue)

    def _handle_finish(self, task_id: str) -> None:
        if task := self._scheduled_cleanups.pop(task_id, None):
            task.cancel()
        self._running_tasks.pop(task_id, None)

    def _run_not_found_error(self, task_id: str | None) -> Exception:
        return RuntimeError(
            f"Run for task ID {task_id} not found. "
            + "It may be on another replica, make sure to enable sticky sessions in your load balancer"
        )

    async def _schedule_run_cleanup(self, request_context: RequestContext):
        task_id, context_id = request_context.task_id, request_context.context_id
        assert task_id and context_id

        async def cleanup_fn():
            await asyncio.sleep(self._task_timeout.total_seconds())
            if not (run := self._running_tasks.get(task_id)):
                return
            try:
                while not run.done:
                    if run.last_invocation + self._task_timeout < datetime.now():
                        logger.warning(f"Task {task_id} did not finish in {self._task_timeout}")
                        queue = EventQueue()
                        await run.cancel(request_context=request_context, event_queue=queue)
                        # the original request queue is closed at this point, we need to propagate state to store manually
                        manager = TaskManager(
                            task_id=task_id, context_id=context_id, task_store=self._task_store, initial_message=None
                        )
                        event = await queue.dequeue_event(no_wait=True)
                        if not isinstance(event, TaskStatusUpdateEvent) or event.status.state != TaskState.canceled:
                            raise RuntimeError(f"Something strange occured during scheduled cancel, event: {event}")
                        _ = await manager.save_task_event(event)
                        break
                    await asyncio.sleep(2)
            except Exception as ex:
                logger.error("Error when cleaning up task", exc_info=ex)
            finally:
                _ = self._running_tasks.pop(task_id, None)
                _ = self._scheduled_cleanups.pop(task_id, None)

        self._scheduled_cleanups[task_id] = asyncio.create_task(cleanup_fn())
        self._scheduled_cleanups[task_id].add_done_callback(lambda _: ...)
