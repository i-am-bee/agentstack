/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension } from '@a2a-js/sdk';

import type { A2AServiceExtension, A2AUiExtension } from './types';

export function extractUiExtensionData<U extends string, D>(extension: A2AUiExtension<U, D>) {
  const schema = extension.getMessageMetadataSchema();
  const uri = extension.getUri();

  return function (metadata: Record<string, unknown> | undefined) {
    const { success, data: parsed } = schema.safeParse(metadata ?? {});

    if (!success) {
      return null;
    }

    return parsed[uri];
  };
}

export function extractServiceExtensionDemands<U extends string, D, F>(extension: A2AServiceExtension<U, D, F>) {
  const schema = extension.getDemandsSchema();
  const uri = extension.getUri();

  return function (agentExtensions: AgentExtension[]) {
    const foundExtension = agentExtensions.find((agentExtension) => agentExtension.uri === uri);
    const { success, data: parsed } = schema.safeParse(foundExtension?.params ?? {});

    if (!success) {
      return null;
    }

    return parsed;
  };
}

export function fulfillServiceExtensionDemand<U extends string, D, F>(extension: A2AServiceExtension<U, D, F>) {
  const schema = extension.getFulfillmentSchema();
  const uri = extension.getUri();

  return function (metadata: Record<string, unknown>, fulfillment: F) {
    const { success, data: parsed, error } = schema.safeParse(fulfillment);

    if (!success) {
      console.warn(error);
    }

    return {
      ...metadata,
      [uri]: success ? parsed : {},
    };
  };
}
