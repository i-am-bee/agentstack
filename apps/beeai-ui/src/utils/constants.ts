/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parseNav } from '#modules/nav/parseNav.ts';

export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? '';

export const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? 'http://localhost:3000';

export const APP_FAVICON_SVG = process.env.NEXT_PUBLIC_APP_FAVICON_SVG ?? '/bee.svg';

export const NAV_ITEMS = parseNav(process.env.NEXT_PUBLIC_NAV_ITEMS);

export const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8333';

export const PROD_MODE = process.env.NODE_ENV === 'production';

export const GET_SUPPORT_LINK = 'https://github.com/i-am-bee/beeai-platform/discussions/categories/q-a';

export const DOCUMENTATION_LINK = 'https://docs.beeai.dev';

export const BEE_AI_FRAMEWORK_TAG = 'BeeAI';

export const TRY_LOCALLY_LINK = `${DOCUMENTATION_LINK}/introduction/quickstart`;

export const RUN_LINK = `${DOCUMENTATION_LINK}/how-to/run-agents`;

export const COMPOSE_LINK = `${DOCUMENTATION_LINK}/how-to/compose-agents`;

export const LF_PROJECTS_LINK = 'https://lfprojects.org/';

export const OIDC_ENABLED = process.env.OIDC_ENABLED === 'true';
