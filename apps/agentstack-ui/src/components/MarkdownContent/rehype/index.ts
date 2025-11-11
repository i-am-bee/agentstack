/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import rehypeKatex from 'rehype-katex';
import type { PluggableList } from 'unified';

import { rehypeInlineCode } from './rehypeInlineCode';

export const rehypePlugins = [rehypeKatex, rehypeInlineCode] satisfies PluggableList;
