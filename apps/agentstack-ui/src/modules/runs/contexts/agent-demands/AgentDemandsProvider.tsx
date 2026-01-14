/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type FormFulfillments, ModelCapability, type SettingsValues } from 'agentstack-sdk';
import { type PropsWithChildren, useCallback, useMemo, useRef, useState } from 'react';

import { useListConnectors } from '#modules/connectors/api/queries/useListConnectors.ts';
import type { RunFormValues } from '#modules/form/types.ts';
import { useMatchModelProviders } from '#modules/platform-context/api/mutations/useMatchModelProviders.ts';
import { getSettingsDemandsDefaultValues } from '#modules/runs/settings/utils.ts';

import { useA2AClient } from '../a2a-client';
import { useAgentSecrets } from '../agent-secrets';
import type { FulfillmentsContext } from './agent-demands-context';
import { AgentDemandsContext } from './agent-demands-context';
import { buildFulfillments } from './build-fulfillments';

export function AgentDemandsProvider({ children }: PropsWithChildren) {
  const { agentClient, contextToken } = useA2AClient();
  const { demandedSecrets } = useAgentSecrets();

  const [selectedEmbeddingProviders, setSelectedEmbeddingProviders] = useState<Record<string, string>>({});
  const [selectedLLMProviders, setSelectedLLMProviders] = useState<Record<string, string>>({});
  const formFulfillmentsRef = useRef<FormFulfillments>({ form_fulfillments: {} });

  const [selectedSettings, setSelectedSettings] = useState<SettingsValues>(
    getSettingsDemandsDefaultValues(agentClient.demands.settingsDemands ?? { fields: [] }),
  );

  const onUpdateSettings = useCallback((value: SettingsValues) => {
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

  const {
    data: matchedLLMProviders,
    isPending: isLLMProvidersPending,
    isEnabled: isLLMProvidersEnabled,
  } = useMatchModelProviders({
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

  const {
    data: matchedEmbeddingProviders,
    isPending: isEmbeddingProvidersPending,
    isEnabled: isEmbeddingProvidersEnabled,
  } = useMatchModelProviders({
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
      if (!contextToken) {
        throw new Error('Context token is not available');
      }

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

  const value = useMemo(
    () => ({
      llmProviders: {
        isEnabled: isLLMProvidersEnabled,
        isLoading: isLLMProvidersEnabled && isLLMProvidersPending,
        matched: matchedLLMProviders,
        selected: selectedLLMProviders,
        select: selectLLMProvider,
      },
      embeddingProviders: {
        isEnabled: isEmbeddingProvidersEnabled,
        isLoading: isEmbeddingProvidersEnabled && isEmbeddingProvidersPending,
        matched: matchedEmbeddingProviders,
        selected: selectedEmbeddingProviders,
        select: selectEmbeddingProvider,
      },
      provideFormValues,
      getFulfillments,
      selectedSettings,
      settingsDemands: agentClient?.demands.settingsDemands ?? null,
      formDemands: agentClient?.demands.formDemands ?? null,
      onUpdateSettings,
    }),
    [
      agentClient,
      getFulfillments,
      isEmbeddingProvidersEnabled,
      isEmbeddingProvidersPending,
      isLLMProvidersEnabled,
      isLLMProvidersPending,
      matchedEmbeddingProviders,
      matchedLLMProviders,
      onUpdateSettings,
      provideFormValues,
      selectEmbeddingProvider,
      selectLLMProvider,
      selectedEmbeddingProviders,
      selectedLLMProviders,
      selectedSettings,
    ],
  );

  return <AgentDemandsContext.Provider value={value}>{children}</AgentDemandsContext.Provider>;
}
