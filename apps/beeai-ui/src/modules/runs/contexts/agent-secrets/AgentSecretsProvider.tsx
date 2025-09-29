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
import { useUpdateVariable } from '#modules/variables/api/mutations/useUpdateVariable.ts';
import { useListVariables } from '#modules/variables/api/queries/useListVariables.ts';

import { AgentSecretsContext } from './agent-secrets-context';
import type { AgentRequestSecrets, NonReadySecretDemand, ReadySecretDemand } from './types';

interface Props {
  agent: Agent;
  agentClient?: AgentA2AClient;
}

const STORAGE_KEY = '@i-am-bee/beeai/AGENT-SECRETS-SETTINGS';

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
  const [agentSecrets, setAgentSecrets] = useLocalStorage<Secrets>(STORAGE_KEY, {}, secretsLocalStorageOptions);

  const { data } = useListVariables({ providerId: agent.provider.id });
  const variables = data ? data.variables : null;

  const { mutate: updateVariable } = useUpdateVariable();

  const hasSeenModal = useMemo(() => {
    return agentSecrets[agent.provider.id]?.modalSeen ?? false;
  }, [agentSecrets, agent.provider.id]);

  const secretDemands = useMemo(() => {
    return agentClient?.secretDemands ?? null;
  }, [agentClient]);

  const updateSecret = useCallback(
    (key: string, value: string) => {
      updateVariable({
        providerId: agent.provider.id,
        body: { [key]: value },
      });
    },
    [agent.provider.id, updateVariable],
  );

  const storeSecrets = useCallback(
    (secrets: Record<string, string>) => {
      updateVariable({
        providerId: agent.provider.id,
        body: secrets,
      });
    },
    [agent.provider.id, updateVariable],
  );

  const markModalAsSeen = useCallback(() => {
    setAgentSecrets((prev) => ({
      ...prev,
      [agent.provider.id]: {
        modalSeen: true,
      },
    }));
  }, [agent.provider.id, setAgentSecrets]);

  const secrets = useMemo(() => {
    if (secretDemands === null) {
      return [];
    }

    return Object.entries(secretDemands).map(([key, demand]) => {
      if (variables && key in variables) {
        const readyDemand: ReadySecretDemand = {
          ...demand,
          isReady: true,
          value: variables[key],
        };

        return { key, ...readyDemand };
      } else {
        const nonReadyDemand: NonReadySecretDemand = {
          ...demand,
          isReady: false,
        };

        return { key, ...nonReadyDemand };
      }
    });
  }, [secretDemands, variables]);

  const getRequestSecrets = useCallback((): AgentRequestSecrets => {
    return secrets.reduce<AgentRequestSecrets>((acc, secret) => {
      return { ...acc, [secret.key]: secret };
    }, {});
  }, [secrets]);

  const contextValue = useMemo(
    () => ({
      secrets,
      hasSeenModal,
      markModalAsSeen,
      getRequestSecrets,
      updateSecret,
      storeSecrets,
    }),
    [secrets, hasSeenModal, markModalAsSeen, getRequestSecrets, updateSecret, storeSecrets],
  );

  return <AgentSecretsContext.Provider value={contextValue}>{children}</AgentSecretsContext.Provider>;
}
