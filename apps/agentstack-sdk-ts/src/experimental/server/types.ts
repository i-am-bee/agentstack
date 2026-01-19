/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, Message, Part, TaskStatus, TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { AgentDetail } from '../../shared/extensions/ui/agent-detail';
import type { RunContext } from './context';
import type { ExtensionConfig } from './extensions/types';

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
  handler: AgentFunction<TDeps>;
  version?: string;
}

export interface ServerOptions {
  host?: string;
  port?: number;
  selfRegistrationId?: string;
  platformUrl?: string;
}

export interface ServerHandle {
  close: () => Promise<void>;
  port: number;
  url: string;
}
