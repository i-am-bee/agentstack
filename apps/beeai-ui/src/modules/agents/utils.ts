/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Provider } from '#modules/providers/api/types.ts';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings } from '#utils/helpers.ts';

import type { AgentExtension, AgentMetadata, UiExtension } from './api/types';
import { type Agent, AGENT_EXTENSION_UI_KEY } from './api/types';

export const getAgentsProgrammingLanguages = (agents: Agent[] | undefined) => {
  // TODO: a2a
  // return uniq(
  //   agents
  //     ?.map(({ metadata }) => metadata?.programming_language)
  //     .filter(isNotNull)
  //     .flat(),
  // );
  if (agents) {
  }
  return [];
};

export function getAgentSourceCodeUrl(agent: Agent) {
  // TODO: a2a
  if (agent) {
  }

  return null;
  // const { links } = agent.metadata;
  // const link = links?.find(({ type }) => type === LinkType.SourceCode);

  // return link?.url;
}

export function sortAgentsByName(a: Agent, b: Agent) {
  return compareStrings(a.name, b.name);
}

export function isAgentUiSupported(agent: Agent) {
  const ui_type = agent.ui?.ui_type;

  return ui_type && SupportedUis.includes(ui_type);
}

// TODO: a2a
type AgentLinkType = 'homepage' | 'documentation' | 'source-code';

export function getAvailableAgentLinkUrl<T extends AgentLinkType | AgentLinkType[]>(
  metadata: AgentMetadata,
  type: T,
): string | undefined {
  // TODO: a2a
  // const typesArray = Array.isArray(type) ? type : [type];

  // let url: string | undefined;
  // for (const type of typesArray) {
  //   url = metadata.links?.find((link) => link.type === type)?.url;
  //   if (url) {
  //     break;
  //   }
  // }

  // return url;
  if (metadata && type) {
  }
  return undefined;
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
