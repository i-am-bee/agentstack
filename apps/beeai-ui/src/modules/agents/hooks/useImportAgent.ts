/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { flushSync } from 'react-dom';

import { useCreateProviderBuild } from '#modules/provider-builds/api/mutations/useCreateProviderBuild.ts';
import { usePreviewProviderBuild } from '#modules/provider-builds/api/mutations/usePreviewProviderBuild.ts';
import { useProviderBuild } from '#modules/provider-builds/api/queries/useProviderBuild.ts';
import { useProviderBuildLogs } from '#modules/provider-builds/api/queries/useProviderBuildLogs.ts';
import type { ProviderBuild } from '#modules/provider-builds/api/types.ts';
import { useImportProvider } from '#modules/providers/api/mutations/useImportProvider.ts';
import { useListProviders } from '#modules/providers/api/queries/useListProviders.ts';
import type { Provider } from '#modules/providers/api/types.ts';
import { ProviderSourcePrefixes } from '#modules/providers/constants.ts';
import { ProviderSource } from '#modules/providers/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useAgent } from '../api/queries/useAgent';
import type { ImportAgentFormValues } from '../types';

export function useImportAgent() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [providerOrigin, setProviderOrigin] = useState<string | null>(null);
  const [buildId, setBuildId] = useState<string>();

  const [actionRequired, setActionRequired] = useState(false);
  const [providersToUpdate, setProvidersToUpdate] = useState<Provider[]>();

  const {
    isFetching: isProvidersFetching,
    error: providersError,
    refetch: fetchProviders,
  } = useListProviders({
    query: { origin: providerOrigin ? encodeURI(providerOrigin) : null },
    enabled: false,
  });
  const { data: build } = useProviderBuild({ id: buildId });
  const { data: buildLogs } = useProviderBuildLogs({ id: buildId });

  const buildStatus = build?.status;
  const buildErrorMessage = build?.error_message;

  const {
    mutateAsync: previewProviderBuild,
    isPending: isPreviewPending,
    error: previewError,
  } = usePreviewProviderBuild();

  const {
    mutateAsync: createProviderBuild,
    isPending: isCreateBuildPending,
    error: buildError,
  } = useCreateProviderBuild();

  const {
    data: importedProvider,
    mutateAsync: importProvider,
    isPending: isImportPending,
    error: importError,
  } = useImportProvider();

  const providerId = importedProvider?.id ?? build?.provider_id;

  const { data: agent } = useAgent({ providerId });

  const logs = useMemo(
    () =>
      buildLogs
        ?.map(({ data }) => {
          const parsed = maybeParseJson(data);

          if (!parsed) {
            return null;
          }

          const { type, value } = parsed;

          if (type === 'json') {
            const json = JSON.parse(value);
            const message = json.message;

            if (message && typeof message === 'string') {
              return message;
            }
          }

          return value;
        })
        .filter(isNotNull) ?? [],
    [buildLogs],
  );

  const isBuildPending = useMemo(
    () => isCreateBuildPending || (buildId && buildStatus !== 'completed' && buildStatus !== 'failed'),
    [isCreateBuildPending, buildId, buildStatus],
  );

  const isPending = useMemo(
    () => isPreviewPending || isProvidersFetching || isBuildPending || isImportPending || Boolean(providerId && !agent),
    [isPreviewPending, isProvidersFetching, isBuildPending, isImportPending, providerId, agent],
  );

  const resetState = useCallback(() => {
    setErrorMessage(null);
    setProviderOrigin(null);
    setBuildId(undefined);
    setActionRequired(false);
    setProvidersToUpdate(undefined);
  }, []);

  const createBuild = useCallback(
    async ({
      location,
      action = 'add_provider',
      providerId = '',
    }: Pick<ImportAgentFormValues, 'location' | 'action' | 'providerId'>) => {
      let onCompleteAction: ProviderBuild['on_complete'] = { type: 'no_action' };

      switch (action) {
        case 'update_provider':
          onCompleteAction = { type: 'update_provider', provider_id: providerId };

          break;
        case 'add_provider':
          onCompleteAction = { type: 'add_provider' };

          break;
      }

      const createdBuild = await createProviderBuild({ location, on_complete: onCompleteAction });

      setBuildId(createdBuild?.id);
    },
    [createProviderBuild],
  );

  const importAgent = useCallback(
    async ({ source, location, action, providerId }: ImportAgentFormValues) => {
      resetState();

      if (source === ProviderSource.GitHub) {
        if (action) {
          createBuild({ location, action, providerId });

          return;
        }

        const buildPreview = await previewProviderBuild({ location });

        if (!buildPreview) {
          return;
        }

        const { provider_origin: providerOrigin, destination } = buildPreview;

        flushSync(() => setProviderOrigin(providerOrigin));

        const { data: providers } = await fetchProviders();

        if (!providers) {
          return;
        }

        const { total_count: providersCount, items } = providers;
        const provider = items.find((provider) => provider.source === destination);

        if (provider) {
          setErrorMessage(`Duplicate provider found: source='${destination}' already exists`);

          return;
        }

        if (providersCount !== 0) {
          setActionRequired(true);
          setProvidersToUpdate(items);

          return;
        }

        createBuild({ location, action });
      } else if (source === ProviderSource.Docker) {
        await importProvider({ location: `${ProviderSourcePrefixes[source]}${location}` });
      }
    },
    [resetState, previewProviderBuild, fetchProviders, createBuild, importProvider],
  );

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
    const normalizedBuildError = buildErrorMessage ? new Error(buildErrorMessage) : buildError;

    const error = importError ?? normalizedBuildError ?? providersError ?? previewError;

    if (error) {
      setErrorMessage(error.message);
    }
  }, [buildErrorMessage, buildError, importError, providersError, previewError]);

  return {
    agent,
    logs,
    actionRequired,
    providersToUpdate,
    isPending,
    error,
    importAgent,
  };
}
