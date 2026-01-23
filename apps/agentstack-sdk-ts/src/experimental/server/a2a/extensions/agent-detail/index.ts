/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AGENT_DETAIL_EXTENSION_URI } from '../../../../../extensions';
import type { ExtensionSpec } from '../../../core/extensions/types';
import type { AgentDetailExtensionFulfillments, AgentDetailExtensionParams } from './types';

export class AgentDetailExtensionSpec implements ExtensionSpec<
  AgentDetailExtensionParams,
  AgentDetailExtensionFulfillments
> {
  readonly uri = AGENT_DETAIL_EXTENSION_URI;
  readonly params: AgentDetailExtensionParams;

  constructor(params: AgentDetailExtensionParams) {
    this.params = {
      ...params,
      programming_language: params.programming_language ?? 'TypeScript',
    };
  }

  toAgentCardExtension() {
    return {
      uri: this.uri,
      required: false,
      params: this.params,
    };
  }

  parseFulfillments() {
    return undefined;
  }
}
