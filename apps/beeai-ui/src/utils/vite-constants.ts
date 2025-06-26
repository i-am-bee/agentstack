/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parseNav } from '#modules/nav/parseNav.ts';

export const APP_NAME = __APP_NAME__;

export const NAV = parseNav(__NAV__);

export const PHOENIX_SERVER_TARGET = __PHOENIX_SERVER_TARGET__;

export const PROD_MODE = import.meta.env.PROD;
