/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  Artifact,
  Message,
  Part,
  Task,
  TaskArtifactUpdateEvent,
  TaskStatus,
  TaskStatusUpdateEvent,
} from '@a2a-js/sdk';
import type { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';

import { RunContext } from './context';
import type { ExtensionConfig, ExtensionServer } from './extensions/types';
import type { AgentFunction, RunYield } from './types';

function createMessage(taskId: string, contextId: string, parts: Part[], metadata?: Record<string, unknown>): Message {
  return {
    kind: 'message',
    messageId: crypto.randomUUID(),
    role: 'agent',
    taskId,
    contextId,
    parts,
    metadata,
  };
}

function createTextPart(text: string): Part {
  return { kind: 'text', text };
}

function createStatusUpdateEvent(
  taskId: string,
  contextId: string,
  status: TaskStatus,
  final: boolean,
): TaskStatusUpdateEvent {
  return {
    kind: 'status-update',
    taskId,
    contextId,
    status,
    final,
  };
}

function createArtifactUpdateEvent(
  taskId: string,
  contextId: string,
  artifact: Artifact,
  lastChunk: boolean,
  append: boolean,
): TaskArtifactUpdateEvent {
  return {
    kind: 'artifact-update',
    taskId,
    contextId,
    artifact,
    lastChunk,
    append,
  };
}

function isAsyncIterable<T>(value: unknown): value is AsyncIterable<T> {
  return value != null && typeof value === 'object' && Symbol.asyncIterator in value;
}

function isMessage(value: unknown): value is Message {
  return value != null && typeof value === 'object' && 'kind' in value && value.kind === 'message';
}

function isPart(value: unknown): value is Part {
  return (
    value != null &&
    typeof value === 'object' &&
    'kind' in value &&
    ['text', 'file', 'data'].includes((value as Part).kind)
  );
}

function isTaskStatus(value: unknown): value is TaskStatus {
  return value != null && typeof value === 'object' && 'state' in value;
}

function isTaskStatusUpdateEvent(value: unknown): value is TaskStatusUpdateEvent {
  return value != null && typeof value === 'object' && 'kind' in value && value.kind === 'status-update';
}

function isArtifact(value: unknown): value is Artifact {
  return value != null && typeof value === 'object' && 'artifactId' in value && 'parts' in value;
}

export class AgentExecutorImpl<TDeps> implements AgentExecutor {
  private readonly handler: AgentFunction<TDeps>;
  private readonly extensions?: ExtensionConfig<TDeps>;
  private readonly runningTasks: Map<string, { cancelled: boolean }> = new Map();

  constructor(handler: AgentFunction<TDeps>, extensions?: ExtensionConfig<TDeps>) {
    this.handler = handler;
    this.extensions = extensions;
  }

  private getOrCreateTask(requestContext: RequestContext, eventBus: ExecutionEventBus): Task {
    if (!requestContext.task) {
      const initialTask: Task = {
        kind: 'task',
        id: requestContext.taskId,
        contextId: requestContext.contextId,
        status: {
          state: 'submitted',
          timestamp: new Date().toISOString(),
        },
        history: [],
      };

      eventBus.publish(initialTask);
      eventBus.publish(createStatusUpdateEvent(initialTask.id, requestContext.contextId, { state: 'working' }, false));

      return initialTask;
    } else {
      return requestContext.task;
    }
  }

  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { userMessage, contextId } = requestContext;

    const task = this.getOrCreateTask(requestContext, eventBus);
    const runContext = new RunContext(task.id, contextId, task);

    const taskState = { cancelled: false };
    this.runningTasks.set(task.id, taskState);

    try {
      const deps = this.resolveExtensions(userMessage);

      const result = this.handler(userMessage, runContext, deps);

      if (isAsyncIterable(result)) {
        for await (const yielded of result) {
          if (taskState.cancelled) {
            this.publishCancelled(eventBus, task.id, contextId);
            return;
          }
          this.processYield(eventBus, task.id, contextId, yielded);
        }
      } else {
        const awaited = await result;
        if (awaited !== undefined) {
          this.processYield(eventBus, task.id, contextId, awaited);
        }
      }

      if (!taskState.cancelled) {
        eventBus.publish(createStatusUpdateEvent(task.id, contextId, { state: 'completed' }, true));
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? createMessage(task.id, contextId, [createTextPart(error.message)])
          : createMessage(task.id, contextId, [createTextPart('Unknown error')]);
      eventBus.publish(createStatusUpdateEvent(task.id, contextId, { state: 'failed', message }, true));
      this.runningTasks.delete(task.id);
    } finally {
      eventBus.finished();
    }
  }

  async cancelTask(taskId: string): Promise<void> {
    const taskState = this.runningTasks.get(taskId);
    if (taskState) {
      taskState.cancelled = true;
    }
  }

  private resolveExtensions(message: Message): TDeps {
    if (!this.extensions) {
      return {} as TDeps;
    }

    const deps: Record<string, unknown> = {};
    for (const [key, ext] of Object.entries(this.extensions) as [
      string,
      ExtensionServer<unknown, unknown, unknown>,
    ][]) {
      const fulfillments = ext.spec.parseFulfillments(message);
      deps[key] = ext.resolveDeps(fulfillments);
    }
    return deps as TDeps;
  }

  private publishCancelled(eventBus: ExecutionEventBus, taskId: string, contextId: string): void {
    eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'canceled' }, true));
  }

  private processYield(eventBus: ExecutionEventBus, taskId: string, contextId: string, yielded: RunYield): void {
    if (typeof yielded === 'string') {
      const message = createMessage(taskId, contextId, [createTextPart(yielded)]);
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'working', message }, false));
    } else if (yielded instanceof Error) {
      const message = createMessage(taskId, contextId, [createTextPart(yielded.message)]);
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'failed', message }, true));
    } else if (isMessage(yielded)) {
      const message: Message = {
        ...yielded,
        taskId,
        contextId,
      };
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'working', message }, false));
    } else if (isPart(yielded)) {
      const message = createMessage(taskId, contextId, [yielded]);
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'working', message }, false));
    } else if (isTaskStatusUpdateEvent(yielded)) {
      eventBus.publish(yielded);
    } else if (isTaskStatus(yielded)) {
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, yielded, false));
    } else if (isArtifact(yielded)) {
      eventBus.publish(createArtifactUpdateEvent(taskId, contextId, yielded, true, false));
    } else if (typeof yielded === 'object' && yielded !== null) {
      const message = createMessage(taskId, contextId, [{ kind: 'data', data: yielded }]);
      eventBus.publish(createStatusUpdateEvent(taskId, contextId, { state: 'working', message }, false));
    }
  }
}
