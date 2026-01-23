/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  Artifact,
  DataPart,
  Message,
  Part,
  TaskArtifactUpdateEvent,
  TaskStatus,
  TaskStatusUpdateEvent,
  TextPart,
} from '@a2a-js/sdk';
import { randomUUID } from 'crypto';

export function createMessage({
  taskId,
  contextId,
  parts,
  metadata,
}: {
  taskId: string;
  contextId: string;
  parts: Part[];
  metadata?: Record<string, unknown>;
}): Message {
  return {
    kind: 'message',
    messageId: randomUUID(),
    role: 'agent',
    taskId,
    contextId,
    parts,
    metadata,
  };
}

export function createTextPart(text: string): TextPart {
  return {
    kind: 'text',
    text,
  };
}

export function createDataPart(data: Record<string, unknown>): DataPart {
  return {
    kind: 'data',
    data,
  };
}

export function createStatusUpdateEvent({
  taskId,
  contextId,
  status,
  final,
}: {
  taskId: string;
  contextId: string;
  status: TaskStatus;
  final: boolean;
}): TaskStatusUpdateEvent {
  return {
    kind: 'status-update',
    taskId,
    contextId,
    status,
    final,
  };
}

export function createArtifactUpdateEvent({
  taskId,
  contextId,
  artifact,
  lastChunk,
  append,
}: {
  taskId: string;
  contextId: string;
  artifact: Artifact;
  lastChunk: boolean;
  append: boolean;
}): TaskArtifactUpdateEvent {
  return {
    kind: 'artifact-update',
    taskId,
    contextId,
    artifact,
    lastChunk,
    append,
  };
}
