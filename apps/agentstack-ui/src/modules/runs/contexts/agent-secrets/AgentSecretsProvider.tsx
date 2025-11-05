/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useListVariables } from '#modules/variables/api/queries/useListVariables.ts';

import { AgentSecretsContext } from './agent-secrets-context';
import type { NonReadySecretDemand, ReadySecretDemand } from './types';

interface Props {
  agentClient?: AgentA2AClient;
}

export function AgentSecretsProvider({ agentClient, children }: PropsWithChildren<Props>) {
  const { data } = useListVariables();
  const variables = data ? data.variables : null;

  const secretDemands = useMemo(() => {
    return agentClient?.demands.secretDemands ?? null;
  }, [agentClient]);

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
      demandedSecrets,
    }),
    [demandedSecrets],
  );

  return <AgentSecretsContext.Provider value={contextValue}>{children}</AgentSecretsContext.Provider>;
}
