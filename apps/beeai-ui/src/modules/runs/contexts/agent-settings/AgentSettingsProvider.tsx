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

import { AgentSettingsContext } from './agent-settings-context';
import type { AgentRequestedApiKeys, NonReadySecretDemand, ReadySecretDemand } from './types';

interface Props {
  agent: Agent;
  agentClient?: AgentA2AClient;
}

const secretsSchema = z.record(z.string(), z.record(z.string(), z.string()));
type Secrets = z.infer<typeof secretsSchema>;

const secretsLocalStorageOptions = {
  serializer: (value: Secrets) => JSON.stringify(value),
  deserializer: (value) => secretsSchema.parse(JSON.parse(value)),
};

export function AgentSettingsProvider({ agent, agentClient, children }: PropsWithChildren<Props>) {
  const [agentSettings, setAgentSettings] = useLocalStorage<Secrets>('agent-settings', {}, secretsLocalStorageOptions);

  const parsedAgentSettings = useMemo(() => {
    return agentSettings[agent.provider.id] ?? {};
  }, [agentSettings, agent.provider.id]);

  const secretDemands = useMemo(() => {
    return agentClient?.secretDemands ?? null;
  }, [agentClient]);

  const updateApiKey = useCallback(
    (key: string, value: string) => {
      setAgentSettings((prev) => ({ ...prev, [agent.provider.id]: { ...prev[agent.provider.id], [key]: value } }));
    },
    [agent.provider.id, setAgentSettings],
  );

  const provideSecrets = useCallback(
    (secrets: Record<string, string>) => {
      setAgentSettings((prev) => ({ ...prev, [agent.provider.id]: { ...prev[agent.provider.id], ...secrets } }));
    },
    [agent.provider.id, setAgentSettings],
  );

  const revokeApiKey = useCallback(
    (key: string) => {
      setAgentSettings((prev) => {
        const providerSettings = { ...prev[agent.provider.id] };
        delete providerSettings[key];

        return { ...prev, [agent.provider.id]: providerSettings };
      });
    },
    [agent.provider.id, setAgentSettings],
  );

  const requestedApiKeys = useMemo(() => {
    if (secretDemands === null) {
      return {};
    }

    return Object.entries(secretDemands).reduce<AgentRequestedApiKeys>((acc, [key, demand]) => {
      if (parsedAgentSettings[key]) {
        const readyDemand: ReadySecretDemand = {
          ...demand,
          isReady: true,
          value: parsedAgentSettings[key],
        };

        acc[key] = readyDemand;
      } else {
        const nonReadyDemand: NonReadySecretDemand = {
          ...demand,
          isReady: false,
        };

        acc[key] = nonReadyDemand;
      }
      return acc;
    }, {});
  }, [secretDemands, parsedAgentSettings]);

  const contextValue = useMemo(
    () => ({
      requestedApiKeys,
      updateApiKey,
      revokeApiKey,
      provideSecrets,
    }),
    [requestedApiKeys, updateApiKey, revokeApiKey, provideSecrets],
  );

  return <AgentSettingsContext.Provider value={contextValue}>{children}</AgentSettingsContext.Provider>;
}
