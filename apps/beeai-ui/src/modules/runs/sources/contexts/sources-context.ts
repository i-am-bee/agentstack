/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext, type Dispatch, type SetStateAction } from 'react';

import type { SourcesData } from '../api/types';
import type { ActiveMessageKey, ActiveSourceKey } from './types';

export const SourcesContext = createContext<SourcesContextValue>({
  sourcesData: {},
  activeMessageKey: null,
  activeSourceKey: null,
});

interface SourcesContextValue {
  sourcesData: SourcesData;
  activeMessageKey: ActiveMessageKey;
  activeSourceKey: ActiveSourceKey;
  setActiveMessageKey?: Dispatch<SetStateAction<ActiveMessageKey>>;
  setActiveSourceKey?: Dispatch<SetStateAction<ActiveSourceKey>>;
}
