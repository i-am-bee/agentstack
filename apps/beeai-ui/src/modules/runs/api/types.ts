/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

export type CreateRunRequest = ApiRequest<'/api/v1/acp/runs'>;

export type CreateRunStreamRequest = Omit<CreateRunRequest, 'mode'> & { mode: RunMode.Stream };

export type CreateRunResponse = ApiResponse<'/api/v1/acp/runs', 'post'>;

export type ReadRunPath = ApiPath<'/api/v1/acp/runs/{run_id}'>;

export type ReadRunResponse = ApiResponse<'/api/v1/acp/runs/{run_id}'>;

export type ResumeRunPath = ApiPath<'/api/v1/acp/runs/{run_id}', 'post'>;

export type ResumeRunRequest = ApiRequest<'/api/v1/acp/runs/{run_id}'>;

export type CancelRunPath = ApiPath<'/api/v1/acp/runs/{run_id}/cancel', 'post'>;

export type Message = CreateRunRequest['input'][number];

export type MessagePart = Message['parts'][number] & { metadata?: MessagePartMetadata };

export type MessagePartMetadata = CitationMetadata;

export type Artifact = Exclude<MessagePart, 'name'> & { name: string };

export interface CitationMetadata {
  kind: MetadataKind.Citation;
  data: {
    url: string;
    start_index: number;
    end_index: number;
  };
}

export type RunId = CreateRunResponse['run_id'];

export type SessionId = CreateRunResponse['session_id'];

export enum MetadataKind {
  Citation = 'citation',
}

export enum RunMode {
  Sync = 'sync',
  Async = 'async',
  Stream = 'stream',
}

export enum RunStatus {
  Created = 'created',
  InProgress = 'in-progress',
  Awaiting = 'awaiting',
  Cancelling = 'cancelling',
  Cancelled = 'cancelled',
  Completed = 'completed',
  Failed = 'failed',
}

export enum EventType {
  RunCreated = 'run.created',
  RunInProgress = 'run.in-progress',
  RunAwaiting = 'run.awaiting',
  RunFailed = 'run.failed',
  RunCancelled = 'run.cancelled',
  RunCompleted = 'run.completed',
  MessageCreated = 'message.created',
  MessagePart = 'message.part',
  MessageCompleted = 'message.completed',
  Generic = 'generic',
}

export interface RunCreatedEvent {
  type: EventType.RunCreated;
  run: ReadRunResponse;
}

export interface RunInProgressEvent {
  type: EventType.RunInProgress;
  run: ReadRunResponse;
}

export interface RunAwaitingEvent {
  type: EventType.RunAwaiting;
  run: ReadRunResponse;
}

export interface RunFailedEvent {
  type: EventType.RunFailed;
  run: ReadRunResponse;
}

export interface RunCancelledEvent {
  type: EventType.RunCancelled;
  run: ReadRunResponse;
}

export interface RunCompletedEvent {
  type: EventType.RunCompleted;
  run: ReadRunResponse;
}

export interface MessageCreatedEvent {
  type: EventType.MessageCreated;
  message: Message;
}

export interface ArtifactEvent {
  type: EventType.MessagePart;
  part: Artifact;
}

export interface MessagePartEvent {
  type: EventType.MessagePart;
  part: MessagePart;
}

export interface MessageCompletedEvent {
  type: EventType.MessageCompleted;
  message: Message;
}

export interface GenericEvent {
  type: EventType.Generic;
  generic: {
    // TODO: We should probably narrow this down for each UI type
    thought?: string;
    tool_name?: string;
    tool_input?: string;
    tool_output?: string;
    message?: string;
    agent_idx?: number;
  } & {
    [key: string]: unknown;
  };
}

export type RunEvent =
  | RunCreatedEvent
  | RunInProgressEvent
  | RunAwaitingEvent
  | RunFailedEvent
  | RunCancelledEvent
  | RunCompletedEvent
  | MessageCreatedEvent
  | ArtifactEvent
  | MessagePartEvent
  | MessageCompletedEvent
  | GenericEvent;
