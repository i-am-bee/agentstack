/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension } from '@a2a-js/sdk';

import type { ExtensionSpec } from './types';

const PLATFORM_SELF_REGISTRATION_URI =
  'https://a2a-extensions.agentstack.beeai.dev/services/platform-self-registration/v1';

export interface PlatformSelfRegistrationParams {
  self_registration_id: string;
}

class PlatformSelfRegistrationExtensionSpec implements ExtensionSpec<PlatformSelfRegistrationParams, undefined> {
  public readonly uri = PLATFORM_SELF_REGISTRATION_URI;
  public readonly params: PlatformSelfRegistrationParams;

  constructor(params: PlatformSelfRegistrationParams) {
    this.params = params;
  }

  toAgentCardExtension(): AgentExtension {
    return {
      uri: this.uri,
      required: false,
      params: {
        self_registration_id: this.params.self_registration_id,
      },
    };
  }

  parseFulfillments(): undefined {
    return undefined;
  }
}

export function createPlatformSelfRegistrationExtension(
  selfRegistrationId: string,
): PlatformSelfRegistrationExtensionSpec {
  return new PlatformSelfRegistrationExtensionSpec({ self_registration_id: selfRegistrationId });
}
