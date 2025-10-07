/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import uniq from 'lodash/uniq';
import uniqWith from 'lodash/uniqWith';

import { agentDetailExtension } from '#api/a2a/extensions/ui/agent-detail.ts';
import { extractUiExtensionData } from '#api/a2a/extensions/utils.ts';
import type { Provider } from '#modules/providers/api/types.ts';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings, isNotNull } from '#utils/helpers.ts';

import type { Agent, AgentExtension } from './api/types';

const extractAgentDetail = extractUiExtensionData(agentDetailExtension);

export const getAgentsProgrammingLanguages = (agents: Agent[] | undefined) => {
  return uniq(
    agents
      ?.map(({ ui }) => ui.programming_language)
      .filter(isNotNull)
      .flat(),
  );
};

export function sortAgentsByName(a: Agent, b: Agent) {
  return compareStrings(a.name, b.name);
}

export function isAgentUiSupported(agent: Agent) {
  const interaction_mode = agent.ui?.interaction_mode;

  return interaction_mode && SupportedUis.includes(interaction_mode);
}

export function getAgentDetail(extensions: AgentExtension[]) {
  const uri = agentDetailExtension.getUri();
  const metadata = extensions.find((extension) => extension.uri === uri)?.params;

  if (!metadata) {
    return {};
  }

  return extractAgentDetail({ [uri]: metadata }) ?? {};
}

export function buildAgent(provider: Provider): Agent {
  const { agent_card, ...providerData } = provider;

  const extensions = agent_card.capabilities.extensions ?? [];
  const ui = getAgentDetail(extensions);

  return {
    ...agent_card,
    provider: { ...providerData, metadata: agent_card.provider },
    ui,
  };
}

export function getAgentTags(agent: Agent) {
  return uniqWith(
    agent.skills.flatMap(({ tags }) => tags),
    (a, b) => a.toLocaleLowerCase() === b.toLocaleLowerCase(),
  );
}

export function getAgentPromptExamples(agent: Agent) {
  return uniqWith(
    agent.skills.flatMap(({ examples }) => examples).filter(isNotNull),
    (a, b) => a.toLocaleLowerCase() === b.toLocaleLowerCase(),
  );
}
