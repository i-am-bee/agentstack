/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? '';

export const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? 'http://localhost:3000';

export const APP_FAVICON_SVG = process.env.NEXT_PUBLIC_APP_FAVICON_SVG ?? '/bee.svg';

export const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8333';

export const PROD_MODE = process.env.NODE_ENV === 'production';

export const GET_SUPPORT_LINK = 'https://github.com/i-am-bee/agentstack/discussions/categories/q-a';

export const DOCUMENTATION_LINK = 'https://docs.beeai.dev';

export const LF_PROJECTS_LINK = 'https://lfprojects.org/';

export const TRUST_PROXY_HEADERS = (process.env.TRUST_PROXY_HEADERS ?? 'false').toLowerCase() === 'true';

export const NEXTAUTH_URL = process.env.NEXTAUTH_URL ? new URL(process.env.NEXTAUTH_URL) : undefined;

export const THEME_STORAGE_KEY = '@i-am-bee/agentstack/THEME';

export const AGENT_SECRETS_SETTINGS_STORAGE_KEY = '@i-am-bee/agentstack/AGENT-SECRETS-SETTINGS';

export const MODEL_SETUP_COMMAND = 'agentstack model setup';
