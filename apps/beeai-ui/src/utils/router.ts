/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FEATURE_FLAGS } from './constants';
import { parseFeatureFlags } from './feature-flags';

const featureFlags = parseFeatureFlags(FEATURE_FLAGS);

export const routes = {
  home: () => '/' as const,
  notFound: () => '/not-found' as const,
  agents: () => `/${sections.agents}` as const,
  agentRun: ({ name }: { name: string }) =>
    featureFlags.QueryParamAgentRouting ? `/${sections.agents}?agentName=${name}` : `/${sections.agents}/${name}`,
  playground: () => `/${sections.playground}` as const,
  playgroundSequential: () => `/${sections.playground}/sequential` as const,
  settings: () => '/settings' as const,
};

export const sections = { agents: 'agents', playground: 'playground' } as const;
export type NavSectionName = (typeof sections)[keyof typeof sections];
