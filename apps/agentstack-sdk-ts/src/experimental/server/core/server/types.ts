/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard, Artifact, Message, Part, TaskStatus, TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { buildApiClient } from '../../../../api';
import type { AgentDetail } from '../../../../client/a2a/extensions/ui/agent-detail/types';
import type { RunContext } from '../context';
import type { ExtensionConfig } from '../extensions/types';

export type RunYield =
  | string
  | Message
  | Part
  | TaskStatus
  | TaskStatusUpdateEvent
  | Artifact
  | Error
  | Record<string, unknown>;

export type AgentFunction<TDeps = Record<string, never>> = (
  input: Message,
  ctx: RunContext,
  deps: TDeps,
) => AsyncIterable<RunYield> | Promise<RunYield | void>;

export interface AgentOptions<TDeps = Record<string, never>> {
  name: string;
  description?: string;
  detail?: AgentDetail;
  extensions?: ExtensionConfig<TDeps>;
  version?: string;
  protocolVersion?: string;
  handler: AgentFunction<TDeps>;
}

export interface ServerOptions {
  host?: string;
  port?: number;
  selfRegistrationId?: string;
  platformUrl?: string;
}

export interface ServerHandle {
  port: number;
  url: string;
  close: () => Promise<void>;
}

export interface AutoregistrationOptions {
  selfRegistrationId: string;
  agentCard: AgentCard;
  host: string;
  port: number;
  api: ReturnType<typeof buildApiClient>;
}
