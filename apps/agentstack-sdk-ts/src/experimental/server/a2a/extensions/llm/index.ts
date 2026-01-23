/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Message } from '@a2a-js/sdk';

import { LLM_EXTENSION_URI, llmFulfillmentsSchema } from '../../../../../extensions';
import type { ExtensionServer, ExtensionSpec } from '../../../core/extensions/types';
import type { LLMExtensionDeps, LLMExtensionFulfillments, LLMExtensionParams } from './types';

export class LLMExtensionSpec implements ExtensionSpec<LLMExtensionParams, LLMExtensionFulfillments> {
  readonly uri = LLM_EXTENSION_URI;
  readonly params: LLMExtensionParams;
  readonly fulfillmentsSchema = llmFulfillmentsSchema;

  constructor(params: LLMExtensionParams) {
    this.params = params;
  }

  toAgentCardExtension() {
    return {
      uri: this.uri,
      required: true,
      params: {
        llm_demands: this.params.demands,
      },
    };
  }

  parseFulfillments(message: Message) {
    const { metadata } = message;

    if (!metadata) {
      return undefined;
    }

    const extensionData = metadata[this.uri];

    if (!extensionData) {
      return undefined;
    }

    const { success, data } = this.fulfillmentsSchema.safeParse(extensionData);

    if (!success) {
      return undefined;
    }

    return data;
  }
}

export class LLMExtensionServer implements ExtensionServer<
  LLMExtensionDeps,
  LLMExtensionParams,
  LLMExtensionFulfillments
> {
  readonly spec: LLMExtensionSpec;

  constructor(params: LLMExtensionParams) {
    this.spec = new LLMExtensionSpec(params);
  }

  resolveDeps(fulfillments: LLMExtensionFulfillments | undefined): LLMExtensionDeps {
    return {
      fulfillments: fulfillments?.llm_fulfillments,
    };
  }
}
