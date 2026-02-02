/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ExtendKcContext } from 'keycloakify/login';

import type { KcEnvName, ThemeName } from '../kc.gen';

export type KcContextExtension = {
  themeName: ThemeName;
  properties: Record<KcEnvName, string>;
  // NOTE: Here you can declare more properties to extend the KcContext
  // See: https://docs.keycloakify.dev/faq-and-help/some-values-you-need-are-missing-from-in-kccontext
};

export type KcContextExtensionPerPage = Record<string, Record<string, unknown>>;

export type KcContext = ExtendKcContext<KcContextExtension, KcContextExtensionPerPage>;
