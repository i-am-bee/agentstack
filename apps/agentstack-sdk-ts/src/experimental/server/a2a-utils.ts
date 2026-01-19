/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, Message, Part, TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent } from '@a2a-js/sdk';

export function createMessage(
  taskId: string,
  contextId: string,
  parts: Part[],
  metadata?: Record<string, unknown>,
): Message {
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

export function createTextPart(text: string): Part {
  return { kind: 'text', text };
}

export function createStatusUpdateEvent(
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

export function createArtifactUpdateEvent(
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

export function isAsyncIterable<T>(value: unknown): value is AsyncIterable<T> {
  return value != null && typeof value === 'object' && Symbol.asyncIterator in value;
}

export function isMessage(value: unknown): value is Message {
  return value != null && typeof value === 'object' && 'kind' in value && value.kind === 'message';
}

export function isPart(value: unknown): value is Part {
  return (
    value != null &&
    typeof value === 'object' &&
    'kind' in value &&
    ['text', 'file', 'data'].includes((value as Part).kind)
  );
}

export function isTaskStatus(value: unknown): value is TaskStatus {
  return value != null && typeof value === 'object' && 'state' in value;
}

export function isTaskStatusUpdateEvent(value: unknown): value is TaskStatusUpdateEvent {
  return value != null && typeof value === 'object' && 'kind' in value && value.kind === 'status-update';
}

export function isArtifact(value: unknown): value is Artifact {
  return value != null && typeof value === 'object' && 'artifactId' in value && 'parts' in value;
}
