/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard } from '@a2a-js/sdk';

import { ApiErrorType, buildApiClient } from '../../client/api/core';

const MAX_RETRY_ATTEMPTS = 10;
const VARIABLE_RELOAD_INTERVAL_MS = 5000;

export interface AutoRegistrationOptions {
  platformUrl: string;
  selfRegistrationId: string;
  agentCard: AgentCard;
  host: string;
  port: number;
}

export class AutoRegistration {
  private providerId: string | null = null;
  private variableReloadInterval: ReturnType<typeof setInterval> | null = null;
  private configuredVariables: Set<string> = new Set();
  private stopped = false;
  private readonly api: ReturnType<typeof buildApiClient>;
  private readonly options: AutoRegistrationOptions;

  constructor(options: AutoRegistrationOptions) {
    this.options = options;
    this.api = buildApiClient({ baseUrl: options.platformUrl });
  }

  private get productionMode(): boolean {
    return process.env.PRODUCTION_MODE?.toLowerCase() === 'true' || process.env.PRODUCTION_MODE === '1';
  }

  private buildProviderLocation(): string {
    const host = this.options.host.replace(/0\.0\.0\.0|localhost|127\.0\.0\.1/g, 'host.docker.internal');
    return `http://${host}:${this.options.port}#${this.options.selfRegistrationId}`;
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async withRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < MAX_RETRY_ATTEMPTS; attempt++) {
      if (this.stopped) {
        throw new Error('AutoRegistration stopped');
      }

      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
        console.log(`Registration attempt ${attempt + 1} failed, retrying in ${delay}ms...`);
        await this.sleep(delay);
      }
    }

    throw lastError ?? new Error('Max retry attempts exceeded');
  }

  async register(): Promise<void> {
    if (this.productionMode) {
      console.log('Agent is not automatically registered in production mode.');
      return;
    }

    const location = this.buildProviderLocation();
    console.log('Registering agent to the agentstack platform', { location });

    try {
      await this.withRetry(async () => {
        const existingResult = await this.api.readProviderByLocation({
          location: encodeURIComponent(location),
        });

        if (existingResult.ok) {
          const patchResult = await this.api.patchProvider({
            id: existingResult.data.id,
            agent_card: this.options.agentCard,
          });

          if (!patchResult.ok) {
            throw new Error(`Failed to patch provider: ${patchResult.error.message}`);
          }

          this.providerId = patchResult.data.id;
        } else if (existingResult.error.type === ApiErrorType.Http && existingResult.error.response?.status === 404) {
          const createResult = await this.api.createProvider({
            location,
            agent_card: this.options.agentCard,
          });

          if (!createResult.ok) {
            throw new Error(`Failed to create provider: ${createResult.error.message}`);
          }

          this.providerId = createResult.data.id;
        } else {
          throw new Error(`Failed to lookup provider: ${existingResult.error.message}`);
        }
      });

      console.log('Agent registered successfully');
      await this.loadVariables(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Agent can not be registered to agentstack server: ${message}`);
    }
  }

  async loadVariables(firstRun = false): Promise<void> {
    if (!this.providerId) {
      return;
    }

    try {
      const result = await this.api.listProviderVariables({ id: this.providerId });

      if (!result.ok) {
        console.log(`Failed to load variables: ${result.error.message}`);
        return;
      }

      const variables = result.data.variables ?? {};
      const oldVariables = new Set(this.configuredVariables);

      for (const variable of this.configuredVariables) {
        if (!(variable in variables)) {
          delete process.env[variable];
          this.configuredVariables.delete(variable);
        }
      }

      for (const [key, value] of Object.entries(variables)) {
        process.env[key] = value;
        this.configuredVariables.add(key);
      }

      const dirty =
        oldVariables.size !== this.configuredVariables.size ||
        [...oldVariables].some((v) => !this.configuredVariables.has(v));

      if (dirty) {
        console.log(`Environment variables reloaded dynamically: ${[...this.configuredVariables].join(', ')}`);
      }

      if (firstRun && this.configuredVariables.size > 0) {
        console.log('Environment variables loaded dynamically.');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`Failed to load variables: ${message}`);
    }
  }

  startVariableReload(): void {
    if (this.productionMode) {
      return;
    }

    this.variableReloadInterval = setInterval(() => {
      this.loadVariables().catch(() => {});
    }, VARIABLE_RELOAD_INTERVAL_MS);
  }

  stop(): void {
    this.stopped = true;

    if (this.variableReloadInterval) {
      clearInterval(this.variableReloadInterval);
      this.variableReloadInterval = null;
    }
  }
}
