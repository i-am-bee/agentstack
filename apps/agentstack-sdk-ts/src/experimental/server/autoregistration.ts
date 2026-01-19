/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard } from '@a2a-js/sdk';

import type { buildApiClient } from '../../client/api/core';
import { ApiErrorType } from '../../client/api/core';
import { isProductionMode } from './config';
import { withRetry } from './utils';

const VARIABLE_RELOAD_INTERVAL_MS = 5000;

export interface AutoregistrationOptions {
  selfRegistrationId: string;
  agentCard: AgentCard;
  host: string;
  port: number;
  api: ReturnType<typeof buildApiClient>;
}

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
}

export function createAutoregisterToAgentstack(options: AutoregistrationOptions): () => void {
  const { selfRegistrationId, agentCard, host, port, api } = options;
  let providerId: string | null = null;
  let variableReloadInterval: ReturnType<typeof setInterval> | null = null;
  let configuredVariables = new Set<string>();
  let stopped = false;

  function buildProviderLocation(): string {
    const normalizedHost = host.replace(/0\.0\.0\.0|localhost|127\.0\.0\.1/g, 'host.docker.internal');
    return `http://${normalizedHost}:${port}#${selfRegistrationId}`;
  }

  async function loadVariables(firstRun = false): Promise<void> {
    if (!providerId) {
      return;
    }

    try {
      const result = await api.listProviderVariables({ id: providerId });

      if (!result.ok) {
        console.warn(`Failed to load variables: ${result.error.message}`);
        return;
      }

      const variables = result.data.variables ?? {};
      const oldVariables = configuredVariables;
      const newVariables = new Set<string>();

      for (const variable of configuredVariables) {
        if (!(variable in variables)) {
          delete process.env[variable];
        }
      }

      for (const [key, value] of Object.entries(variables)) {
        process.env[key] = value;
        newVariables.add(key);
      }

      const dirty = !setsEqual(oldVariables, newVariables);
      configuredVariables = newVariables;

      if (dirty && configuredVariables.size > 0) {
        console.log(`Environment variables reloaded: ${[...configuredVariables].join(', ')}`);
      }

      if (firstRun && configuredVariables.size > 0) {
        console.log('Environment variables loaded.');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`Failed to load variables: ${message}`);
    }
  }

  async function register(): Promise<void> {
    if (isProductionMode()) {
      console.log('Agent is not automatically registered in production mode.');
      return;
    }

    const location = buildProviderLocation();
    console.log('Registering agent to the agentstack platform', { location });

    try {
      await withRetry(
        async () => {
          const existingResult = await api.readProviderByLocation({
            location: encodeURIComponent(location),
          });

          if (existingResult.ok) {
            const patchResult = await api.patchProvider({
              id: existingResult.data.id,
              agent_card: agentCard,
            });

            if (!patchResult.ok) {
              throw new Error(`Failed to patch provider: ${patchResult.error.message}`);
            }

            providerId = patchResult.data.id;
          } else if (existingResult.error.type === ApiErrorType.Http && existingResult.error.response?.status === 404) {
            const createResult = await api.createProvider({
              location,
              agent_card: agentCard,
            });

            if (!createResult.ok) {
              throw new Error(`Failed to create provider: ${createResult.error.message}`);
            }

            providerId = createResult.data.id;
          } else {
            throw new Error(`Failed to lookup provider: ${existingResult.error.message}`);
          }
        },
        {
          shouldAbort: () => stopped,
          onRetry: (attempt, _error, delayMs) => {
            console.warn(`Registration attempt ${attempt} failed, retrying in ${delayMs}ms...`);
          },
        },
      );

      console.log('Agent registered successfully');
      await loadVariables(true);

      variableReloadInterval = setInterval(() => {
        loadVariables().catch((error) => console.error('Error during variable reload:', error));
      }, VARIABLE_RELOAD_INTERVAL_MS);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`Agent cannot be registered to agentstack server: ${message}`);
    }
  }

  function stop(): void {
    stopped = true;

    if (variableReloadInterval) {
      clearInterval(variableReloadInterval);
      variableReloadInterval = null;
    }
  }

  register();

  return stop;
}
