/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo } from 'react';
import { useLocalStorage } from 'usehooks-ts';
import z from 'zod';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { useListVariables } from '#modules/variables/api/queries/useListVariables.ts';
import { AGENT_SECRETS_SETTINGS_STORAGE_KEY } from '#utils/constants.ts';

import { AgentSecretsContext } from './agent-secrets-context';
import type { NonReadySecretDemand, ReadySecretDemand } from './types';

interface Props {
  agent: Agent;
  agentClient?: AgentA2AClient;
}

const secretsSchema = z.record(
  z.string(),
  z.object({
    modalSeen: z.boolean().optional(),
  }),
);
type Secrets = z.infer<typeof secretsSchema>;

const secretsLocalStorageOptions = {
  serializer: (value: Secrets) => JSON.stringify(value),
  deserializer: (value) => {
    try {
      return secretsSchema.parse(JSON.parse(value));
    } catch (error) {
      console.warn('Failed to parse agent secrets settings from localStorage', error);
      return {};
    }
  },
};

export function AgentSecretsProvider({ agent, agentClient, children }: PropsWithChildren<Props>) {
  const [agentSecrets, setAgentSecrets] = useLocalStorage<Secrets>(
    AGENT_SECRETS_SETTINGS_STORAGE_KEY,
    {},
    secretsLocalStorageOptions,
  );

  const { data } = useListVariables();
  const variables = data ? data.variables : null;

  const hasSeenModal = useMemo(() => {
    return agentSecrets[agent.provider.id]?.modalSeen ?? false;
  }, [agentSecrets, agent.provider.id]);

  const secretDemands = useMemo(() => {
    return agentClient?.demands.secretDemands ?? null;
  }, [agentClient]);

  const markModalAsSeen = useCallback(() => {
    setAgentSecrets((prev) => ({
      ...prev,
      [agent.provider.id]: {
        modalSeen: true,
      },
    }));
  }, [agent.provider.id, setAgentSecrets]);

  const demandedSecrets = useMemo(() => {
    if (secretDemands === null) {
      return [];
    }

    return Object.entries(secretDemands.secret_demands).map(([key, demand]) => {
      if (variables && key in variables) {
        const readyDemand: ReadySecretDemand = {
          ...demand,
          key,
          isReady: true,
          value: variables[key],
        };

        return readyDemand;
      } else {
        const nonReadyDemand: NonReadySecretDemand = {
          ...demand,
          isReady: false,
        };

        return { key, ...nonReadyDemand };
      }
    });
  }, [secretDemands, variables]);

  const contextValue = useMemo(
    () => ({
      hasSeenModal,
      markModalAsSeen,
      demandedSecrets,
    }),
    [demandedSecrets, hasSeenModal, markModalAsSeen],
  );

  return <AgentSecretsContext.Provider value={contextValue}>{children}</AgentSecretsContext.Provider>;
}
