# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import inspect
import typing
from asyncio import CancelledError
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager, suppress
from datetime import datetime, timedelta
from typing import Any, Final, TypeAlias, TypeVar

import janus
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue, QueueManager
from a2a.server.tasks import TaskManager, TaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentCardSignature,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Artifact,
    Message,
    Part,
    SecurityScheme,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.types.a2a_pb2 import SecurityRequirement
from google.protobuf import message as _message
from typing_extensions import override

from agentstack_sdk.a2a.extensions import AgentDetailExtensionSpec, BaseExtensionServer
from agentstack_sdk.a2a.extensions.ui.agent_detail import (
    AgentDetail,
    AgentDetailExtensionSpec,
    AgentDetailTool,
)
from agentstack_sdk.a2a.extensions.ui.error import (
    get_error_extension_context,
)
from agentstack_sdk.a2a.types import Metadata, RunYield, RunYieldResume, validate_message
from agentstack_sdk.server.constants import _DEFAULT_AGENT_INTERFACE, _DEFAULT_AGENT_SKILL, DEFAULT_IMPLICIT_EXTENSIONS
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.dependencies import Dependency, Depends, extract_dependencies
from agentstack_sdk.server.store.context_store import ContextStore
from agentstack_sdk.server.utils import cancel_task
from agentstack_sdk.types import A2ASecurity
from agentstack_sdk.util.logging import logger

AgentFunction: TypeAlias = Callable[[], AsyncGenerator[RunYield, RunYieldResume]]
AgentFunctionFactory: TypeAlias = Callable[[RequestContext, ContextStore], AbstractAsyncContextManager[AgentFunction]]

OriginalFnType = TypeVar("OriginalFnType", bound=Callable[..., Any])

_IMPLICIT_DEPENDENCY_PREFIX: Final = "___server_dep"


class AgentExecuteFn(typing.Protocol):
    async def __call__(self, _ctx: RunContext, **kwargs: Any) -> None: ...


class ActiveDependenciesContainer:
    def __init__(self, active_dependencies: dict[str, Dependency], run_context: RunContext):
        self._dependencies = active_dependencies
        self._run_context = run_context

    @property
    def user_dependency_args(self):
        return {k: v for k, v in self._dependencies.items() if not k.startswith(_IMPLICIT_DEPENDENCY_PREFIX)}

    def handle_incoming_message(self, message: Message, request_context: RequestContext):
        for dependency in self._dependencies.values():
            if isinstance(dependency, BaseExtensionServer):
                dependency.handle_incoming_message(message, self._run_context, request_context)


class Agent:
    execute_fn: AgentExecuteFn

    def __init__(
        self,
        initial_card: AgentCard,
        detail: AgentDetail,
        dependency_args: dict[str, Depends],
        execute_fn: AgentExecuteFn,
    ) -> None:
        self.execute_fn = execute_fn
        self.initial_card = initial_card
        self._card = initial_card
        self._detail = detail
        self._dependency_args = dependency_args
        self._implicit_extensions: dict[str, BaseExtensionServer] = {}
        self._required_extensions: set[str] = set()
        self._initialized = False

    def initialize(
        self,
        a2a_security: A2ASecurity | None = None,
        supported_interfaces: list[AgentInterface] | None = None,
        implicit_extensions: dict[str, BaseExtensionServer] = DEFAULT_IMPLICIT_EXTENSIONS,
        required_extensions: set[str] | None = None,
    ) -> None:
        if self._initialized:
            raise RuntimeError("Agent already initialized")

        self._implicit_extensions = implicit_extensions
        self._required_extensions = required_extensions or set()

        user_sdk_extensions = {
            dep.extension.spec.URI: dep.extension for dep in self._dependency_args.values() if dep.extension is not None
        }

        self._all_dependencies = {
            **self._dependency_args,
            **{
                f"{_IMPLICIT_DEPENDENCY_PREFIX}{uri}": Depends(dep)
                for uri, dep in self._implicit_extensions.items()
                if uri not in user_sdk_extensions
            },
        }

        self._initialized = True

        capabilities = AgentCapabilities()
        if self.initial_card.HasField("capabilities"):
            capabilities.CopyFrom(self.initial_card.capabilities)

        capabilities.extensions.extend(AgentDetailExtensionSpec(self._detail).to_agent_card_extensions())
        capabilities.extensions.extend(
            e_card
            for ext in self._sdk_extensions
            for e_card in ext.spec.to_agent_card_extensions(
                required=True if ext.spec.URI in self._required_extensions else None
            )
        )

        self._card = AgentCard()
        self._card.CopyFrom(self.initial_card)
        self._card.capabilities.CopyFrom(capabilities)

        if len(self._card.supported_interfaces) == 1 and self._card.supported_interfaces[0] == _DEFAULT_AGENT_INTERFACE:
            if not supported_interfaces:
                raise ValueError("supported_interfaces must be provided when using default agent interface")
            self._card.supported_interfaces.clear()  # type: ignore [attr-defined]
        if supported_interfaces:
            self._card.supported_interfaces.extend(supported_interfaces)
        if a2a_security:
            self._card.security_requirements.extend(a2a_security["security_requirements"])
            for security_key, security_value in a2a_security["security_schemes"].items():
                self._card.security_schemes[security_key].CopyFrom(security_value)

    @property
    def card(self) -> AgentCard:
        if not self._initialized:
            raise RuntimeError("Agent not initialized")
        return self._card

    @property
    def _sdk_extensions(self) -> list[BaseExtensionServer]:
        return [dep.extension for dep in self._all_dependencies.values() if dep.extension is not None]

    @asynccontextmanager
    async def dependency_container(
        self, message: Message, run_context: RunContext, request_context: RequestContext
    ) -> AsyncIterator[ActiveDependenciesContainer]:
        async with AsyncExitStack() as stack:
            initialized_dependencies: dict[str, Dependency] = {}
            initialize_deps_exceptions: list[Exception] = []
            for pname, depends in self._all_dependencies.items():
                # call dependencies with the first message and initialize their lifespan
                try:
                    initialized_dependencies[pname] = await stack.enter_async_context(
                        depends(message, run_context, request_context)
                    )
                except Exception as e:
                    initialize_deps_exceptions.append(e)

            if initialize_deps_exceptions:
                raise (
                    ExceptionGroup("Failed to initialize dependencies", initialize_deps_exceptions)
                    if len(initialize_deps_exceptions) > 1
                    else initialize_deps_exceptions[0]
                )

            yield ActiveDependenciesContainer(initialized_dependencies, run_context)


def agent(
    name: str | None = None,
    description: str | None = None,
    *,
    supported_interfaces: list[AgentInterface] | None = None,
    provider: AgentProvider | None = None,
    version: str | None = None,
    documentation_url: str | None = None,
    capabilities: AgentCapabilities | None = None,
    security_schemes: dict[str, SecurityScheme] | None = None,
    security_requirements: list[SecurityRequirement] | None = None,
    default_input_modes: list[str] | None = None,
    default_output_modes: list[str] | None = None,
    detail: AgentDetail | None = None,
    icon_url: str | None = None,
    skills: list[AgentSkill] | None = None,
    signatures: list[AgentCardSignature] | None = None,
) -> Callable[[OriginalFnType], Agent]:
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

    if capabilities:
        _caps = AgentCapabilities()
        _caps.CopyFrom(capabilities)
        capabilities = _caps
    else:
        capabilities = AgentCapabilities(streaming=True)

    def decorator(fn: OriginalFnType) -> Agent:
        dependencies = extract_dependencies(fn)

        resolved_name = name or fn.__name__
        resolved_description = description or fn.__doc__ or "Description not provided"

        final_detail = detail or AgentDetail()

        if final_detail.tools is None and skills:
            final_detail.tools = [
                AgentDetailTool(name=skill.name, description=skill.description or "") for skill in skills
            ]

        if final_detail.user_greeting is None:
            final_detail.user_greeting = resolved_description

        if final_detail.input_placeholder is None:
            final_detail.input_placeholder = "What is your task?"

        card = AgentCard(
            name=resolved_name,
            description=resolved_description,
            supported_interfaces=supported_interfaces or [_DEFAULT_AGENT_INTERFACE],
            provider=provider,
            capabilities=capabilities,
            security_schemes=security_schemes,
            security_requirements=security_requirements,
            default_input_modes=default_input_modes or ["text"],
            default_output_modes=default_output_modes or ["text"],
            documentation_url=documentation_url,
            icon_url=icon_url,
            skills=skills or [_DEFAULT_AGENT_SKILL],
            signatures=signatures,
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

        return Agent(
            initial_card=card,
            detail=final_detail,
            dependency_args=dependencies,
            execute_fn=execute_fn,
        )

    return decorator


class AgentRun:
    def __init__(self, agent: Agent, context_store: ContextStore, on_finish: Callable[[], None] | None = None) -> None:
        self._agent: Agent = agent
        self._task: asyncio.Task[None] | None = None
        self.last_invocation: datetime = datetime.now()
        self.resume_queue: asyncio.Queue[RunYieldResume] = asyncio.Queue()
        self._run_context: RunContext | None = None
        self._request_context: RequestContext | None = None
        self._task_updater: TaskUpdater | None = None
        self._context_store: ContextStore = context_store
        self._lock: asyncio.Lock = asyncio.Lock()
        self._on_finish: Callable[[], None] | None = on_finish
        self._working: bool = False
        self._dependency_container: ActiveDependenciesContainer | None = None

    @property
    def run_context(self) -> RunContext:
        if not self._run_context:
            raise RuntimeError("Accessing run context for run that has not been started")
        return self._run_context

    @property
    def request_context(self) -> RequestContext:
        if not self._request_context:
            raise RuntimeError("Accessing request context for run that has not been started")
        return self._request_context

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
        async with self._lock:
            if self._working or self.done:
                raise RuntimeError("Attempting to start a run that is already executing or done")
            task_id, context_id, message = request_context.task_id, request_context.context_id, request_context.message
            assert task_id and context_id and message
            context_store = await self._context_store.create(context_id)
            self._run_context = RunContext(
                configuration=request_context.configuration,
                context_id=context_id,
                task_id=task_id,
                current_task=request_context.current_task,
                related_tasks=request_context.related_tasks,
                _store=context_store,
            )
            self._request_context = request_context
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
            assert task_id and context_id and message and self._dependency_container
            self._request_context = request_context
            self._task_updater = TaskUpdater(event_queue, task_id, context_id)

            self._dependency_container.handle_incoming_message(message, request_context)

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

    def _with_context(self, message: Message | None = None) -> Message | None:
        if message:
            message.context_id = self.task_updater.context_id
            message.task_id = self.task_updater.task_id
        return message

    async def _run_agent_function(self, initial_message: Message) -> None:
        yield_queue = self.run_context._yield_queue
        yield_resume_queue = self.run_context._yield_resume_queue

        try:
            async with self._agent.dependency_container(
                initial_message, self.run_context, self.request_context
            ) as dependency_container:
                self._dependency_container = dependency_container
                task = asyncio.create_task(
                    self._agent.execute_fn(self.run_context, **dependency_container.user_dependency_args)
                )
                try:
                    resume_value: RunYieldResume = None
                    opened_artifacts: set[str] = set()
                    while not task.done() or yield_queue.async_q.qsize() > 0:
                        yielded_value = await yield_queue.async_q.get()

                        if isinstance(yielded_value, _message.Message):
                            validate_message(yielded_value)

                        self.last_invocation = datetime.now()

                        match yielded_value:
                            case str(text):
                                await self.task_updater.update_status(
                                    TaskState.TASK_STATE_WORKING,
                                    message=self.task_updater.new_agent_message(parts=[Part(text=text)]),
                                )
                            case Part() as part:
                                await self.task_updater.update_status(
                                    TaskState.TASK_STATE_WORKING,
                                    message=self.task_updater.new_agent_message(parts=[part]),
                                )
                            case Message() as message:
                                await self.task_updater.update_status(
                                    TaskState.TASK_STATE_WORKING, message=self._with_context(message)
                                )
                            case Artifact(parts=parts, artifact_id=artifact_id, name=name, metadata=metadata):
                                last_chunk = True
                                if "_last_chunk" in metadata:
                                    last_chunk = bool(metadata["_last_chunk"])
                                    del metadata["_last_chunk"]
                                append = artifact_id in opened_artifacts
                                if not last_chunk:
                                    opened_artifacts.add(artifact_id)
                                elif artifact_id in opened_artifacts:
                                    opened_artifacts.remove(artifact_id)

                                await self.task_updater.add_artifact(
                                    parts=list(parts),
                                    artifact_id=artifact_id,
                                    name=name,
                                    metadata=dict(metadata),
                                    last_chunk=last_chunk,
                                    append=append,
                                )
                            case TaskStatus(
                                state=(
                                    TaskState.TASK_STATE_AUTH_REQUIRED | TaskState.TASK_STATE_INPUT_REQUIRED
                                ) as state,
                                message=message,
                            ):
                                await self.task_updater.update_status(state=state, message=self._with_context(message))
                                self._working = False
                                resume_value = await self.resume_queue.get()
                                self.resume_queue.task_done()
                            case TaskStatus(state=state, message=message):
                                await self.task_updater.update_status(state=state, message=self._with_context(message))
                            case TaskStatusUpdateEvent(
                                status=TaskStatus(state=state, message=message),
                                metadata=metadata,
                            ):
                                await self.task_updater.update_status(
                                    state=state, message=self._with_context(message), metadata=dict(metadata)
                                )
                            case TaskArtifactUpdateEvent(
                                artifact=Artifact(artifact_id=artifact_id, name=name, metadata=metadata, parts=parts),
                                append=append,
                                last_chunk=last_chunk,
                            ):
                                await self.task_updater.add_artifact(
                                    parts=list(parts),
                                    artifact_id=artifact_id,
                                    name=name,
                                    metadata=dict(metadata),
                                    append=append,
                                    last_chunk=last_chunk,
                                )
                            case Metadata() as metadata:
                                await self.task_updater.update_status(
                                    state=TaskState.TASK_STATE_WORKING,
                                    message=self.task_updater.new_agent_message(parts=[], metadata=metadata),
                                )
                            case dict() as data:
                                from google.protobuf.struct_pb2 import Struct, Value

                                s = Struct()
                                s.update(data)
                                await self.task_updater.update_status(
                                    state=TaskState.TASK_STATE_WORKING,
                                    message=self.task_updater.new_agent_message(
                                        parts=[Part(data=Value(struct_value=s))]
                                    ),
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
                    case TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.TASK_STATE_INPUT_REQUIRED
                            | TaskState.TASK_STATE_AUTH_REQUIRED
                            | TaskState.TASK_STATE_COMPLETED
                            | TaskState.TASK_STATE_FAILED
                            | TaskState.TASK_STATE_CANCELED
                            | TaskState.TASK_STATE_REJECTED
                        )
                    ):
                        break
                    case _:
                        pass

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
            nonlocal task_id
            await asyncio.sleep(self._task_timeout.total_seconds())
            if task_id is None or not (run := self._running_tasks.get(task_id)):
                return
            try:
                while not run.done:
                    if run.last_invocation + self._task_timeout < datetime.now():
                        logger.warning(f"Task {task_id} did not finish in {self._task_timeout}")
                        queue = EventQueue()
                        await run.cancel(request_context=request_context, event_queue=queue)
                        # the original request queue is closed at this point, we need to propagate state to store manually
                        manager = TaskManager(
                            task_id=task_id, context_id=context_id, task_store=self._task_store, initial_message=None,
                            context=request_context.call_context,
                        )
                        event = await queue.dequeue_event(no_wait=True)
                        if (
                            not isinstance(event, TaskStatusUpdateEvent)
                            or event.status.state != TaskState.TASK_STATE_CANCELED
                        ):
                            raise RuntimeError(f"Something strange occured during scheduled cancel, event: {event}")
                        await manager.save_task_event(event)
                        break
                    await asyncio.sleep(2)
            except Exception as ex:
                logger.error("Error when cleaning up task", exc_info=ex)
            finally:
                self._running_tasks.pop(task_id, None)
                self._scheduled_cleanups.pop(task_id, None)

        self._scheduled_cleanups[task_id] = asyncio.create_task(cleanup_fn())
        self._scheduled_cleanups[task_id].add_done_callback(lambda _: ...)
