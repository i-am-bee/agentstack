/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, Message, Part, TaskStatus, TaskStatusUpdateEvent, TextPart } from '@a2a-js/sdk';

function isObjectLike(value: unknown) {
  return value != null && typeof value === 'object';
}

export function isAsyncIterable<T>(value: unknown): value is AsyncIterable<T> {
  return isObjectLike(value) && Symbol.asyncIterator in value;
}

export function isMessage(value: unknown): value is Message {
  return isObjectLike(value) && 'kind' in value && value.kind === 'message';
}

export function isArtifact(value: unknown): value is Artifact {
  return isObjectLike(value) && 'artifactId' in value;
}

export function isPart(value: unknown): value is Part {
  return (
    isObjectLike(value) &&
    'kind' in value &&
    typeof value.kind === 'string' &&
    ['text', 'file', 'data'].includes(value.kind)
  );
}

export function isTextPart(part: Part | undefined): part is TextPart {
  return part != null && part.kind === 'text';
}

export function isTaskStatus(value: unknown): value is TaskStatus {
  return isObjectLike(value) && 'state' in value;
}

export function isTaskStatusUpdateEvent(value: unknown): value is TaskStatusUpdateEvent {
  return isObjectLike(value) && 'kind' in value && value.kind === 'status-update';
}
