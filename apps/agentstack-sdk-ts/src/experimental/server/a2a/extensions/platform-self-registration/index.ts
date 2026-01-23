/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ExtensionSpec } from '../../../core/extensions/types';
import type { PlatformSelfRegistrationExtensionFulfillments, PlatformSelfRegistrationExtensionParams } from './types';

export const PLATFORM_SELF_REGISTRATION_EXTENSION_URI =
  'https://a2a-extensions.agentstack.beeai.dev/services/platform-self-registration/v1';

export class PlatformSelfRegistrationExtensionSpec implements ExtensionSpec<
  PlatformSelfRegistrationExtensionParams,
  PlatformSelfRegistrationExtensionFulfillments
> {
  readonly uri = PLATFORM_SELF_REGISTRATION_EXTENSION_URI;
  readonly params: PlatformSelfRegistrationExtensionParams;

  constructor(params: PlatformSelfRegistrationExtensionParams) {
    this.params = params;
  }

  toAgentCardExtension() {
    return {
      uri: this.uri,
      required: false,
      params: this.params,
    };
  }

  parseFulfillments() {
    return undefined;
  }
}
