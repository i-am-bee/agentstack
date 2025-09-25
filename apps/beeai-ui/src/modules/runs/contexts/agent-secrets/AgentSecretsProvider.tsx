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

import { AgentSecretsContext } from './agent-secrets-context';
import type { AgentRequestSecrets, NonReadySecretDemand, ReadySecretDemand } from './types';

interface Props {
  agent: Agent;
  agentClient?: AgentA2AClient;
}

const secretsSchema = z.record(z.string(), z.record(z.string(), z.string()));
type Secrets = z.infer<typeof secretsSchema>;

const secretsLocalStorageOptions = {
  serializer: (value: Secrets) => JSON.stringify(value),
  deserializer: (value) => {
    try {
      return secretsSchema.parse(JSON.parse(value));
    } catch (error) {
      console.warn('Failed to parse agent secrets from localStorage', error);
      return {};
    }
  },
};

export function AgentSecretsProvider({ agent, agentClient, children }: PropsWithChildren<Props>) {
  const [agentSecrets, setAgentSecrets] = useLocalStorage<Secrets>('agent-secrets', {}, secretsLocalStorageOptions);

  const parsedAgentSecrets = useMemo(() => {
    return agentSecrets[agent.provider.id] ?? {};
  }, [agentSecrets, agent.provider.id]);

  const secretDemands = useMemo(() => {
    return agentClient?.secretDemands ?? null;
  }, [agentClient]);

  const updateSecret = useCallback(
    (key: string, value: string) => {
      setAgentSecrets((prev) => ({ ...prev, [agent.provider.id]: { ...prev[agent.provider.id], [key]: value } }));
    },
    [agent.provider.id, setAgentSecrets],
  );

  const storeSecrets = useCallback(
    (secrets: Record<string, string>) => {
      setAgentSecrets((prev) => ({ ...prev, [agent.provider.id]: { ...prev[agent.provider.id], ...secrets } }));
    },
    [agent.provider.id, setAgentSecrets],
  );

  const revokeSecret = useCallback(
    (key: string) => {
      setAgentSecrets((prev) => {
        const providerSettings = { ...prev[agent.provider.id] };
        delete providerSettings[key];

        return { ...prev, [agent.provider.id]: providerSettings };
      });
    },
    [agent.provider.id, setAgentSecrets],
  );

  const secrets = useMemo(() => {
    if (secretDemands === null) {
      return [];
    }

    return Object.entries(secretDemands).map(([key, demand]) => {
      if (parsedAgentSecrets[key]) {
        const readyDemand: ReadySecretDemand = {
          ...demand,
          isReady: true,
          value: parsedAgentSecrets[key],
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
  }, [secretDemands, parsedAgentSecrets]);

  const getRequestSecrets = useCallback((): AgentRequestSecrets => {
    return secrets.reduce<AgentRequestSecrets>((acc, secret) => {
      return { ...acc, [secret.key]: secret };
    }, {});
  }, [secrets]);

  const contextValue = useMemo(
    () => ({
      secrets,
      getRequestSecrets,
      updateSecret,
      revokeSecret,
      storeSecrets,
    }),
    [secrets, getRequestSecrets, updateSecret, revokeSecret, storeSecrets],
  );

  return <AgentSecretsContext.Provider value={contextValue}>{children}</AgentSecretsContext.Provider>;
}
