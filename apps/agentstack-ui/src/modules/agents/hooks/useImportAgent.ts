/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo, useState } from 'react';

import { useImportProvider } from '#modules/providers/api/mutations/useImportProvider.ts';
import { ProviderSourcePrefixes } from '#modules/providers/constants.ts';

import { useAgent } from '../api/queries/useAgent';
import type { ImportAgentFormValues } from '../types';

export function useImportAgent() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    data: importedProvider,
    mutateAsync: importProvider,
    isPending: isImportPending,
    error: importError,
  } = useImportProvider();

  const providerId = importedProvider?.id;

  const { data: agent } = useAgent({ providerId });

  const isPending = isImportPending || Boolean(providerId && !agent);
  const resetState = () => {
    setErrorMessage(null);
  };

  const importAgent = async ({ source, location }: ImportAgentFormValues) => {
    resetState();
    await importProvider({ location: `${ProviderSourcePrefixes[source]}${location}` });
  };

  const error = useMemo(() => {
    if (!errorMessage) {
      return;
    }

    return {
      title: 'Failed to import provider',
      message: errorMessage,
    };
  }, [errorMessage]);

  useEffect(() => {
    if (importError) {
      setErrorMessage(importError.message);
    }
  }, [importError]);

  return {
    agent,
    logs: [] as string[],
    actionRequired: false,
    providersToUpdate: undefined,
    isPending,
    error,
    importAgent,
  };
}
