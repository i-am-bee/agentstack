/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ContextToken } from 'agentstack-sdk';
import { type AgentSettings, type FormFulfillments, ModelCapability } from 'agentstack-sdk';
import { type PropsWithChildren, useCallback, useRef, useState } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useListConnectors } from '#modules/connectors/api/queries/useListConnectors.ts';
import type { RunFormValues } from '#modules/form/types.ts';
import { useMatchProviders } from '#modules/platform-context/api/mutations/useMatchProviders.ts';
import { getSettingsDemandsDefaultValues } from '#modules/runs/settings/utils.ts';

import { useAgentSecrets } from '../agent-secrets';
import type { FulfillmentsContext } from './agent-demands-context';
import { AgentDemandsContext } from './agent-demands-context';
import { buildFulfillments } from './build-fulfillments';

interface Props<UIGenericPart> {
  agentClient: AgentA2AClient<UIGenericPart>;
  contextToken: ContextToken;
}

export function AgentDemandsProvider<UIGenericPart>({
  agentClient,
  contextToken,
  children,
}: PropsWithChildren<Props<UIGenericPart>>) {
  const { demandedSecrets } = useAgentSecrets();

  const [selectedEmbeddingProviders, setSelectedEmbeddingProviders] = useState<Record<string, string>>({});
  const [selectedLLMProviders, setSelectedLLMProviders] = useState<Record<string, string>>({});
  const formFulfillmentsRef = useRef<FormFulfillments>({ form_fulfillments: {} });

  const [selectedSettings, setSelectedSettings] = useState<AgentSettings>(
    getSettingsDemandsDefaultValues(agentClient.demands.settingsDemands ?? { fields: [] }),
  );

  const onUpdateSettings = useCallback((value: AgentSettings) => {
    setSelectedSettings(value);
  }, []);

  const setDefaultSelectedLLMProviders = useCallback(
    (data: Record<string, string[]>) => {
      setSelectedLLMProviders(
        Object.fromEntries(
          Object.entries(data).map(([key, value]) => {
            if (value.length === 0) {
              throw new Error(`No match found for demand ${key}`);
            }

            return [key, value[0]];
          }),
        ),
      );
    },
    [setSelectedLLMProviders],
  );

  const { data: matchedLLMProviders } = useMatchProviders({
    demands: agentClient?.demands.llmDemands?.llm_demands ?? {},
    onSuccess: setDefaultSelectedLLMProviders,
    capability: ModelCapability.Llm,
  });

  const setDefaultSelectedEmbeddingProviders = useCallback(
    (data: Record<string, string[]>) => {
      setSelectedEmbeddingProviders(
        Object.fromEntries(
          Object.entries(data).map(([key, value]) => {
            if (value.length === 0) {
              throw new Error(`No match found for demand ${key}`);
            }

            return [key, value[0]];
          }),
        ),
      );
    },
    [setSelectedEmbeddingProviders],
  );

  const { data: matchedEmbeddingProviders } = useMatchProviders({
    demands: agentClient?.demands.embeddingDemands?.embedding_demands ?? {},
    onSuccess: setDefaultSelectedEmbeddingProviders,
    capability: ModelCapability.Embedding,
  });

  const selectLLMProvider = useCallback(
    (key: string, value: string) => {
      setSelectedLLMProviders((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedLLMProviders],
  );

  const selectEmbeddingProvider = useCallback(
    (key: string, value: string) => {
      setSelectedEmbeddingProviders((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedEmbeddingProviders],
  );

  const provideFormValues = useCallback((values: RunFormValues) => {
    formFulfillmentsRef.current = { form_fulfillments: { initial_form: { values } } };
  }, []);

  const { data: connectorsData } = useListConnectors();

  const getFulfillments = useCallback(
    async (fulfillmentsContext: FulfillmentsContext) => {
      const providedSecrets = demandedSecrets.reduce((memo, secret) => {
        if (secret.isReady) {
          memo[secret.key] = secret.value;
        }
        return memo;
      }, fulfillmentsContext.providedSecrets ?? {});

      const { oauthRedirectUri } = fulfillmentsContext;

      return buildFulfillments({
        contextToken,
        selectedLLMProviders,
        selectedEmbeddingProviders,
        providedSecrets,
        selectedSettings,
        formFulfillments: formFulfillmentsRef.current,
        oauthRedirectUri: oauthRedirectUri ?? null,
        connectors: connectorsData?.items ?? [],
      });
    },
    [contextToken, selectedLLMProviders, selectedEmbeddingProviders, selectedSettings, demandedSecrets, connectorsData],
  );

  return (
    <AgentDemandsContext.Provider
      value={{
        matchedLLMProviders,
        selectedLLMProviders,
        matchedEmbeddingProviders,
        selectedEmbeddingProviders,
        provideFormValues,
        getFulfillments,
        selectLLMProvider,
        selectEmbeddingProvider,
        selectedSettings,
        settingsDemands: agentClient?.demands.settingsDemands ?? null,
        formDemands: agentClient?.demands.formDemands ?? null,
        onUpdateSettings,
      }}
    >
      {children}
    </AgentDemandsContext.Provider>
  );
}
