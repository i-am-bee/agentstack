/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use server';
import { notFound } from 'next/navigation';

import { ErrorWithResponse } from '#api/errors.ts';
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
    console.error('Error fetching agent:', error);

    if (error instanceof ErrorWithResponse) {
      const responseCode = error.response?.status;
      if (responseCode === 404 || responseCode === 422) {
        notFound();
      }
    }

    throw error;
  }

  if (!agent) {
    notFound();
  }

  return agent;
}
