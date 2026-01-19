/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension, Message } from '@a2a-js/sdk';
import type { z } from 'zod';

export interface ExtensionSpec<TParams = unknown, TFulfillments = unknown> {
  uri: string;
  params?: TParams;
  paramsSchema?: z.ZodSchema<TParams>;
  fulfillmentsSchema?: z.ZodSchema<TFulfillments>;
  toAgentCardExtension(): AgentExtension;
  parseFulfillments(message: Message): TFulfillments | undefined;
}

export interface ExtensionServer<TDeps = unknown, TParams = unknown, TFulfillments = unknown> {
  spec: ExtensionSpec<TParams, TFulfillments>;
  resolveDeps(fulfillments: TFulfillments | undefined): TDeps;
}

export type ExtensionConfig<TDeps> = {
  [K in keyof TDeps]: ExtensionServer<TDeps[K], unknown, unknown>;
};

export type ResolvedDeps<T extends ExtensionConfig<unknown>> = {
  [K in keyof T]: T[K] extends ExtensionServer<infer D, unknown, unknown> ? D : never;
};
