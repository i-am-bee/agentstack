/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const routeDefinitions = {
  home: () => '/' as const,
  notFound: () => '/not-found' as const,
  agents: () => `/${sections.agents}` as const,
  agentDetail: () => `/${sections.agents}/:agentName` as const,
  agentRun: () => `/${sections.agents}/:agentName/run` as const,
  playground: () => `/${sections.playground}` as const,
  playgroundSequential: () => `/${sections.playground}/sequential` as const,
  settings: () => '/settings' as const,
};

export const routes = {
  ...routeDefinitions,
  agentDetail: ({ name }: { name: string }) => `/${sections.agents}/${name}`,
  agentRun: ({ name }: { name: string }) => `/${sections.agents}/${name}/run`,
};

export const sections = { agents: 'agents', playground: 'playground' } as const;
export type NavSectionName = (typeof sections)[keyof typeof sections];
