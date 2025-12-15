/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import 'server-only';

import { notFound } from 'next/navigation';

import { handleApiError } from '#app/(auth)/rsc.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { buildAgent } from '#modules/agents/utils.ts';
import { readProvider } from '#modules/providers/api/index.ts';

export async function fetchAgent(providerId: string) {
  let agent: Agent | undefined;

  try {
    const provider = await readProvider({ id: providerId });

    if (provider) {
      agent = buildAgent(provider);
    }
  } catch (error) {
    await handleApiError(error);
  }

  if (!agent) {
    notFound();
  }

  return agent;
}
