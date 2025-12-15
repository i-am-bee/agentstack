/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { handleAgentCard } from 'agentstack-sdk';
import type { ReactElement } from 'react';

import { getAgentClient } from '#api/a2a/agent-card.ts';
import { handleApiError } from '#app/(auth)/rsc.tsx';
import { ErrorPage } from '#components/ErrorPage/ErrorPage.tsx';
import { readSystemConfiguration } from '#modules/configuration/api/index.ts';
import { ModelType, NoModelSelectedErrorPage } from '#modules/runs/components/NoModelSelectedErrorPage.tsx';

export async function ensureModelSelected(providerId: string) {
  let ErrorComponent: ReactElement | null = null;

  try {
    const client = await getAgentClient(providerId);
    const card = await client.getAgentCard();

    const {
      demands: { llmDemands, embeddingDemands },
    } = handleAgentCard(card);

    if (llmDemands || embeddingDemands) {
      const config = await readSystemConfiguration();

      if (llmDemands && !config?.default_llm_model) {
        ErrorComponent = <NoModelSelectedErrorPage />;
      } else if (embeddingDemands && !config?.default_embedding_model) {
        ErrorComponent = <NoModelSelectedErrorPage type={ModelType.Embedding} />;
      }
    }
  } catch (error) {
    await handleApiError(error);

    ErrorComponent = <ErrorPage message="There was an error loading system configuration." />;
  }

  return { ErrorComponent };
}
