/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension } from '@a2a-js/sdk';

import { type AgentDetail, agentDetailSchema } from '../../../shared/extensions/ui/agent-detail';
import type { ExtensionSpec } from './types';

const AGENT_DETAIL_URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/agent-detail/v1';

class AgentDetailExtensionSpec implements ExtensionSpec<AgentDetail, undefined> {
  public readonly uri = AGENT_DETAIL_URI;
  public readonly params: AgentDetail;
  public readonly paramsSchema = agentDetailSchema;

  constructor(params: AgentDetail) {
    this.params = {
      ...params,
      programming_language: params.programming_language ?? 'TypeScript',
    };
  }

  toAgentCardExtension(): AgentExtension {
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

export function agentDetailExtension(params: AgentDetail): AgentDetailExtensionSpec {
  return new AgentDetailExtensionSpec(params);
}
