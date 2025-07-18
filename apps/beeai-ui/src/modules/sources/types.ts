/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UISourcePart } from '#modules/messages/types.ts';

export interface SourcesData {
  [messageKey: string]: UISourcePart[];
}

export const CITATION_LINK_PREFIX = 'citation:';
