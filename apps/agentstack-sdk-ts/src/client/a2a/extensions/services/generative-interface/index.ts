/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../../../../core/extensions/types';
import {
  generativeInterfaceDemandsSchema,
  generativeInterfaceFulfillmentsSchema,
  generativeInterfaceSpecSchema,
} from './schemas';
import type { GenerativeInterfaceDemands, GenerativeInterfaceFulfillments, GenerativeInterfaceSpec } from './types';

export const GENERATIVE_INTERFACE_EXTENSION_URI =
  'https://a2a-extensions.agentstack.beeai.dev/services/generative_interface/v1';

export const generativeInterfaceExtension: A2AServiceExtension<
  typeof GENERATIVE_INTERFACE_EXTENSION_URI,
  GenerativeInterfaceDemands,
  GenerativeInterfaceFulfillments
> = {
  getUri: () => GENERATIVE_INTERFACE_EXTENSION_URI,
  getDemandsSchema: () => generativeInterfaceDemandsSchema,
  getFulfillmentsSchema: () => generativeInterfaceFulfillmentsSchema,
};

export const generativeInterfaceUiExtension: A2AUiExtension<
  typeof GENERATIVE_INTERFACE_EXTENSION_URI,
  GenerativeInterfaceSpec
> = {
  getUri: () => GENERATIVE_INTERFACE_EXTENSION_URI,
  getMessageMetadataSchema: () =>
    z.object({ [GENERATIVE_INTERFACE_EXTENSION_URI]: generativeInterfaceSpecSchema }).partial(),
};

export * from './schemas';
export * from './types';
