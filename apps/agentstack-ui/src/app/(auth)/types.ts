/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'next-auth/providers';

export interface ProviderConfig {
  id: string;
  name: string;
  issuer: string;
  client_id: string;
  client_secret: string;
}

export type ProviderWithId = Provider & {
  id: string;
};
