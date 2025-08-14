/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import uniq from 'lodash/uniq';
import uniqWith from 'lodash/uniqWith';

import type { Provider } from '#modules/providers/api/types.ts';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings, isNotNull } from '#utils/helpers.ts';

import { type Agent, AGENT_EXTENSION_URI, type AgentExtension, type UiExtension } from './api/types';

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

function isAgentUiExtension(extension: AgentExtension): extension is UiExtension {
  return extension.uri === AGENT_EXTENSION_URI;
}

export function buildAgent(provider: Provider): Agent {
  const { agent_card, ...providerData } = provider;

  const ui = agent_card.capabilities.extensions?.find(isAgentUiExtension)?.params ?? {};

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
