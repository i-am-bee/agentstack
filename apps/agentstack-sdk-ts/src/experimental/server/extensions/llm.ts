/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension, Message } from '@a2a-js/sdk';

import {
  type LLMDemand,
  type LLMFulfillment,
  type LLMFulfillments,
  llmFulfillmentsSchema,
} from '../../../shared/extensions/services/llm';
import type { ExtensionServer, ExtensionSpec } from './types';

const LLM_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/services/llm/v1';

export interface LLMExtensionParams {
  demands: Record<string, LLMDemand>;
}

export interface LLMDeps {
  fulfillments?: Record<string, LLMFulfillment>;
}

class LLMExtensionSpec implements ExtensionSpec<LLMExtensionParams, LLMFulfillments> {
  public readonly uri = LLM_EXTENSION_URI;
  public readonly params: LLMExtensionParams;
  public readonly fulfillmentsSchema = llmFulfillmentsSchema;

  constructor(params: LLMExtensionParams) {
    this.params = params;
  }

  toAgentCardExtension(): AgentExtension {
    return {
      uri: this.uri,
      required: true,
      params: {
        llm_demands: this.params.demands,
      },
    };
  }

  parseFulfillments(message: Message): LLMFulfillments | undefined {
    const metadata = message.metadata;
    if (!metadata) return undefined;

    const extensionData = metadata[this.uri];
    if (!extensionData) return undefined;

    const result = this.fulfillmentsSchema.safeParse(extensionData);
    if (!result.success) return undefined;

    return result.data;
  }
}

class LLMExtensionServer implements ExtensionServer<LLMDeps, LLMExtensionParams, LLMFulfillments> {
  public readonly spec: LLMExtensionSpec;

  constructor(params: LLMExtensionParams) {
    this.spec = new LLMExtensionSpec(params);
  }

  resolveDeps(fulfillments: LLMFulfillments | undefined): LLMDeps {
    return {
      fulfillments: fulfillments?.llm_fulfillments,
    };
  }
}

export function llmExtension(params: LLMExtensionParams): LLMExtensionServer {
  return new LLMExtensionServer(params);
}
