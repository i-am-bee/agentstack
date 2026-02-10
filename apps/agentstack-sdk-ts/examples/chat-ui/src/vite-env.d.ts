/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

interface ImportMetaEnv {
  readonly VITE_AGENTSTACK_BASE_URL: string;
  readonly VITE_AGENTSTACK_PROVIDER_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
