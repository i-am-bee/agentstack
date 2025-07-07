/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TrajectoryMetadata as ApiTrajectoryMetadata } from 'acp-sdk';

export type {
  Artifact,
  CitationMetadata,
  Message,
  MessageCompletedEvent,
  MessageCreatedEvent,
  MessagePart,
  MessagePartEvent,
  RunAwaitingEvent,
  RunCancelledEvent,
  RunCompletedEvent,
  RunCreatedEvent,
  Event as RunEvent,
  RunFailedEvent,
  RunId,
  RunInProgressEvent,
  RunMode,
  RunStatus,
  SessionId,
} from 'acp-sdk';

export interface TrajectoryMetadata extends ApiTrajectoryMetadata {
  key?: string;
}

export interface GenericEvent {
  type: 'generic';
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
