/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import uniq from 'lodash/uniq';

import type { components } from '#api/schema.js';
import { SupportedUis } from '#modules/runs/constants.ts';
import { compareStrings, isNotNull } from '#utils/helpers.ts';

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
  const uiType = agent.metadata.ui?.type;

  return uiType && SupportedUis.includes(uiType);
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

export function getAgentDisplayName(agent: Agent) {
  const {
    name,
    metadata: { annotations },
  } = agent;

  return annotations?.display_name ?? name;
}
