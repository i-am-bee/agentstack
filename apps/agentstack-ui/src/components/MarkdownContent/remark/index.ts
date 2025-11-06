/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import type { PluggableList } from 'unified';

import { remarkCitationLink } from './remarkCitationLink';
import { remarkExternalLink } from './remarkExternalLink';

export const remarkPlugins = [
  remarkGfm,
  [remarkMath, { singleDollarTextMath: false }],
  remarkCitationLink,
  remarkExternalLink,
] satisfies PluggableList;
