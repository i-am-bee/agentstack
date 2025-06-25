/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import uniq from 'lodash/uniq';

import type { components } from '#api/schema.js';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings, isNotNull } from '#utils/helpers.ts';

import type { UiType } from './api/types';
import { type Agent, LinkType } from './api/types';

export const getAgentsProgrammingLanguages = (agents: Agent[] | undefined) =>
  uniq(
    agents
      ?.map(({ metadata: { programming_language } }) => programming_language)
      .filter(isNotNull)
      .flat(),
  );

export function getAgentStatusMetadata<K extends string>({ agent, keys }: { agent: Agent; keys: K[] }) {
  const status = agent.metadata.status as Record<string, unknown> | undefined;

  return Object.fromEntries(
    keys.map((key) => [key, typeof status?.[key] === 'string' ? (status[key] as string) : null]),
  ) as Record<K, string | null>;
}

export function getAgentSourceCodeUrl(agent: Agent) {
  const { links } = agent.metadata;
  const link = links?.find(({ type }) => type === LinkType.SourceCode);

  return link?.url;
}

export function sortAgentsByName(a: Agent, b: Agent) {
  return compareStrings(a.name, b.name);
}

export function isAgentUiSupported(agent: Agent) {
  const { ui_type } = getAgentUiMetadata(agent);

  return ui_type && SupportedUis.includes(ui_type as UiType);
}

type AgentLinkType = components['schemas']['LinkType'];

export function getAvailableAgentLinkUrl<T extends AgentLinkType | AgentLinkType[]>(
  metadata: components['schemas']['Metadata'],
  type: T,
): string | undefined {
  const typesArray = Array.isArray(type) ? type : [type];

  let url = undefined;
  for (const type of typesArray) {
    url = metadata.links?.find((link) => link.type === type)?.url;
    if (url) {
      break;
    }
  }

  return url;
}

export function getAgentUiMetadata(agent: Agent) {
  const { name, metadata } = agent;
  const beeai_ui = metadata.annotations?.beeai_ui;

  return {
    ...beeai_ui,
    display_name: beeai_ui?.display_name ?? name,
  };
}
