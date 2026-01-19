/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard, AgentExtension } from '@a2a-js/sdk';
import type { Express } from 'express';

import { AutoRegistration } from './autoregistration';
import { AgentExecutorImpl } from './executor';
import { agentDetailExtension } from './extensions/agent-detail';
import { createPlatformSelfRegistrationExtension } from './extensions/platform-self-registration';
import type { ExtensionConfig, ExtensionServer } from './extensions/types';
import type { AgentOptions, ServerOptions } from './types';

type DefaultRequestHandlerType = new (...args: unknown[]) => unknown;
type InMemoryTaskStoreType = new () => unknown;
type A2AExpressAppType = new (handler: unknown) => { setupRoutes: (app: Express) => Express };

async function loadA2AServerModules(): Promise<{
  InMemoryTaskStore: InMemoryTaskStoreType;
  DefaultRequestHandler: DefaultRequestHandlerType;
  A2AExpressApp: A2AExpressAppType;
}> {
  const serverModulePath = '@a2a-js/sdk/server';
  const expressModulePath = '@a2a-js/sdk/server/express';

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const serverModule = await (Function('modulePath', 'return import(modulePath)')(serverModulePath) as Promise<any>);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const expressModule = await (Function('modulePath', 'return import(modulePath)')(expressModulePath) as Promise<any>);

  return {
    InMemoryTaskStore: serverModule.InMemoryTaskStore,
    DefaultRequestHandler: serverModule.DefaultRequestHandler,
    A2AExpressApp: expressModule.A2AExpressApp,
  };
}

export class Server {
  private agentCard?: AgentCard;
  private agentOptions?: AgentOptions<unknown>;
  private agentConfigured = false;

  agent<TDeps>(options: AgentOptions<TDeps>): this {
    if (this.agentConfigured) {
      throw new Error('Agent already configured. Only one agent per server is supported.');
    }

    let extensions = this.buildExtensions(options.extensions as ExtensionConfig<unknown> | undefined);

    if (options.detail) {
      const detailExt = agentDetailExtension(options.detail);
      extensions = [...(extensions ?? []), detailExt.toAgentCardExtension()];
    }

    this.agentCard = {
      name: options.name,
      description: options.description ?? '',
      url: 'http://localhost:8000',
      version: options.version ?? '1.0.0',
      protocolVersion: '0.2.2',
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

  async run(options: ServerOptions = {}): Promise<void> {
    if (!this.agentConfigured || !this.agentCard || !this.agentOptions) {
      throw new Error('No agent configured. Call agent() before run().');
    }

    const host = options.host ?? '0.0.0.0';
    const port = options.port ?? 8000;
    const selfRegistration = options.selfRegistration ?? true;
    const selfRegistrationId = options.selfRegistrationId ?? this.agentCard.name;
    const platformUrl = options.platformUrl ?? process.env.PLATFORM_URL ?? 'http://127.0.0.1:8333';
    const productionMode = process.env.PRODUCTION_MODE?.toLowerCase() === 'true' || process.env.PRODUCTION_MODE === '1';

    this.agentCard.url = `http://${host === '0.0.0.0' ? 'localhost' : host}:${port}`;

    if (selfRegistration && !productionMode) {
      const selfRegExtension = createPlatformSelfRegistrationExtension(selfRegistrationId);
      this.agentCard.capabilities.extensions = [
        ...(this.agentCard.capabilities.extensions ?? []),
        selfRegExtension.toAgentCardExtension(),
      ];
    }

    const { InMemoryTaskStore, DefaultRequestHandler, A2AExpressApp } = await loadA2AServerModules();

    const taskStore = new InMemoryTaskStore();
    const executor = new AgentExecutorImpl(
      this.agentOptions.handler,
      this.agentOptions.extensions as ExtensionConfig<unknown> | undefined,
    );

    const requestHandler = new DefaultRequestHandler(this.agentCard, taskStore, executor);

    const expressApp = new A2AExpressApp(requestHandler);

    const express = await import('express');
    const app: Express = express.default();

    expressApp.setupRoutes(app);

    let autoRegistration: AutoRegistration | undefined;

    if (selfRegistration && !productionMode) {
      autoRegistration = new AutoRegistration({
        platformUrl,
        selfRegistrationId,
        agentCard: this.agentCard,
        host,
        port,
      });
    }

    return new Promise((resolve, reject) => {
      const server = app.listen(port, host, async () => {
        console.log(`Agent "${this.agentCard!.name}" running at http://${host}:${port}`);
        console.log(`Agent card available at http://${host}:${port}/.well-known/agent-card.json`);

        if (autoRegistration) {
          await autoRegistration.register();
          autoRegistration.startVariableReload();
        }

        resolve();
      });

      server.on('error', (error) => {
        autoRegistration?.stop();
        reject(error);
      });

      const cleanup = () => {
        autoRegistration?.stop();
        server.close();
      };

      process.on('SIGTERM', cleanup);
      process.on('SIGINT', cleanup);
    });
  }

  private buildExtensions(extensionConfig?: ExtensionConfig<unknown>): AgentExtension[] | undefined {
    if (!extensionConfig) return undefined;

    const extensions: AgentExtension[] = [];
    for (const ext of Object.values(extensionConfig) as ExtensionServer<unknown, unknown, unknown>[]) {
      extensions.push(ext.spec.toAgentCardExtension());
    }

    return extensions.length > 0 ? extensions : undefined;
  }
}
