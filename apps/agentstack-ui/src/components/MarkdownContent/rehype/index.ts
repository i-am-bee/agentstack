/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PluggableList } from 'unified';

import { rehypeInlineCode } from './rehypeInlineCode';

export const rehypePlugins = [rehypeInlineCode] satisfies PluggableList;
