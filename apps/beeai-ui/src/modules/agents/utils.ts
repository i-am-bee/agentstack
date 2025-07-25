/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import uniq from 'lodash/uniq';

import type { Provider } from '#modules/providers/api/types.ts';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings, isNotNull } from '#utils/helpers.ts';

import { type Agent, AGENT_EXTENSION_UI_KEY, type AgentExtension, AgentLinkType, type UiExtension } from './api/types';

export const getAgentsProgrammingLanguages = (agents: Agent[] | undefined) => {
  return uniq(
    agents
      ?.map(({ ui }) => ui.programming_language)
      .filter(isNotNull)
      .flat(),
  );
};

export function getAgentSourceCodeUrl(agent: Agent) {
  const { links } = agent.ui;
  const link = links?.find(({ type }) => type === AgentLinkType.SourceCode);

  return link?.url;
}

export function sortAgentsByName(a: Agent, b: Agent) {
  return compareStrings(a.name, b.name);
}

export function isAgentUiSupported(agent: Agent) {
  const ui_type = agent.ui?.ui_type;

  return ui_type && SupportedUis.includes(ui_type);
}

function isAgentUiExtension(extension: AgentExtension): extension is UiExtension {
  return extension.uri === AGENT_EXTENSION_UI_KEY;
}

export function buildAgent(provider: Provider): Agent {
  const { agent_card, ...providerData } = provider;

  const ui = agent_card.capabilities.extensions?.find(isAgentUiExtension)?.params ?? null;

  return {
    ...agent_card,
    provider: { ...providerData, metadata: agent_card.provider },
    ui: {
      ...ui,
      display_name: ui?.display_name ?? agent_card.name,
    },
  };
}
