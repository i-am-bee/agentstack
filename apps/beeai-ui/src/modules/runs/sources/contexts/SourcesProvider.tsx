/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { type PropsWithChildren, useEffect, useMemo, useState } from 'react';

import { useApp } from '#contexts/App/index.ts';

import type { SourcesData } from '../api/types';
import { SourcesContext } from './sources-context';
import type { ActiveMessageKey, ActiveSourceKey } from './types';

interface Props {
  sourcesData: SourcesData;
}

export function SourcesProvider({ sourcesData, children }: PropsWithChildren<Props>) {
  const { sourcesPanelOpen } = useApp();
  const [activeMessageKey, setActiveMessageKey] = useState<ActiveMessageKey>(null);
  const [activeSourceKey, setActiveSourceKey] = useState<ActiveSourceKey>(null);

  useEffect(() => {
    if (!sourcesPanelOpen) {
      setActiveSourceKey(null);
    }
  }, [sourcesPanelOpen]);

  const contextValue = useMemo(
    () => ({
      sourcesData,
      activeMessageKey,
      activeSourceKey,
      setActiveMessageKey,
      setActiveSourceKey,
    }),
    [sourcesData, activeMessageKey, activeSourceKey, setActiveMessageKey, setActiveSourceKey],
  );

  return <SourcesContext.Provider value={contextValue}>{children}</SourcesContext.Provider>;
}
