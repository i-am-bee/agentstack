/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard, AgentExtension } from '@a2a-js/sdk';
import { DefaultRequestHandler, InMemoryTaskStore } from '@a2a-js/sdk/server';
import { agentCardHandler, jsonRpcHandler, UserBuilder } from '@a2a-js/sdk/server/express';
import express from 'express';

import { buildApiClient } from '../../../../api';
import { AgentDetailExtensionSpec } from '../../a2a/extensions/agent-detail';
import { PlatformSelfRegistrationExtensionSpec } from '../../a2a/extensions/platform-self-registration';
import { loadConfig } from '../config';
import type { ExtensionConfig, ExtensionServer } from '../extensions/types';
import { createAutoregisterToAgentstack } from './autoregistration';
import { AgentExecutorImpl } from './executor';
import { createAgentCardUrl } from './helpers';
import type { AgentOptions, ServerHandle, ServerOptions } from './types';

export class Server {
  private agentCard?: AgentCard;
  private agentOptions?: AgentOptions<unknown>;
  private agentConfigured = false;

  agent<TDeps>(options: AgentOptions<TDeps>): this {
    if (this.agentConfigured) {
      throw new Error('Agent already configured. Only one agent per server is supported.');
    }

    let extensions = this.buildExtensions(options.extensions);

    if (options.detail) {
      const detailExt = new AgentDetailExtensionSpec(options.detail);

      extensions = [...(extensions ?? []), detailExt.toAgentCardExtension()];
    }

    this.agentCard = {
      name: options.name,
      description: options.description ?? '',
      url: 'http://localhost:8000',
      version: options.version ?? '1.0.0',
      protocolVersion: options.protocolVersion ?? '0.3.0',
      capabilities: {
        streaming: true,
        extensions,
      },
      defaultInputModes: ['text'],
      defaultOutputModes: ['text'],
      skills: [],
    };

    this.agentOptions = options as AgentOptions<unknown>;
    this.agentConfigured = true;

    return this;
  }

  async run(options: ServerOptions = {}): Promise<ServerHandle> {
    if (!this.agentConfigured || !this.agentCard || !this.agentOptions) {
      throw new Error('No agent configured. Call agent() before run().');
    }

    const config = loadConfig();
    const host = options.host ?? '0.0.0.0';
    const port = options.port ?? 8000;
    const selfRegistrationId = options.selfRegistrationId;
    const platformUrl = options.platformUrl ?? config.platformUrl;
    const productionMode = config.productionMode;

    this.agentCard.url = createAgentCardUrl(host, port);

    if (selfRegistrationId && !productionMode) {
      const selfRegExtension = new PlatformSelfRegistrationExtensionSpec({ self_registration_id: selfRegistrationId });

      this.agentCard.capabilities.extensions = [
        ...(this.agentCard.capabilities.extensions ?? []),
        selfRegExtension.toAgentCardExtension(),
      ];
    }

    const taskStore = new InMemoryTaskStore();
    const executor = new AgentExecutorImpl(this.agentOptions.handler, this.agentOptions.extensions);
    const requestHandler = new DefaultRequestHandler(this.agentCard, taskStore, executor);

    const app = express();

    const agentCardPath = `/.well-known/agent-card.json`;

    app.use(jsonRpcHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
    app.use(agentCardPath, agentCardHandler({ agentCardProvider: requestHandler }));

    const api = buildApiClient({ baseUrl: platformUrl });

    let stopAutoregistration: (() => void) | undefined;

    if (selfRegistrationId && !productionMode) {
      stopAutoregistration = createAutoregisterToAgentstack({
        selfRegistrationId,
        agentCard: this.agentCard,
        host,
        port,
        api,
      });
    }

    return new Promise((resolve, reject) => {
      const server = app.listen(port, host, async () => {
        console.log(`Agent "${this.agentCard!.name}" running at http://${host}:${port}`);
        console.log(`Agent card available at http://${host}:${port}${agentCardPath}`);

        const url = createAgentCardUrl(host, port);
        const handle: ServerHandle = {
          port,
          url,
          close: () =>
            new Promise((resolveClose, rejectClose) => {
              stopAutoregistration?.();

              server.close((error) => {
                if (error) {
                  rejectClose(error);
                } else {
                  resolveClose();
                }
              });
            }),
        };

        resolve(handle);
      });

      server.on('error', (error) => {
        stopAutoregistration?.();
        reject(error);
      });

      const cleanup = () => {
        stopAutoregistration?.();
        server.close();
      };

      process.on('SIGTERM', cleanup);
      process.on('SIGINT', cleanup);
    });
  }

  private buildExtensions(extensionConfig: ExtensionConfig | undefined): AgentExtension[] | undefined {
    if (!extensionConfig) {
      return undefined;
    }

    const extensions: AgentExtension[] = [];

    for (const ext of Object.values(extensionConfig) as ExtensionServer[]) {
      extensions.push(ext.spec.toAgentCardExtension());
    }

    if (extensions.length === 0) {
      return undefined;
    }

    return extensions;
  }
}
