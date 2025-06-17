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

import { type PropsWithChildren, useCallback, useMemo, useState } from 'react';

import type { SourcesData } from '../api/types';
import { SourcesContext } from './sources-context';

interface Props {
  data: SourcesData;
}

export function SourcesProvider({ data, children }: PropsWithChildren<Props>) {
  const [activeMessage, setActiveMessage] = useState<string | null>(null);

  const sources = useMemo(() => (activeMessage ? data[activeMessage] : []), [data, activeMessage]);

  const showSources = useCallback((messageKey: string) => {
    setActiveMessage(messageKey);
  }, []);

  const hideSources = useCallback(() => {
    setActiveMessage(null);
  }, []);

  const contextValue = useMemo(
    () => ({
      activeMessage,
      sources,
      showSources,
      hideSources,
    }),
    [activeMessage, sources, showSources, hideSources],
  );

  return <SourcesContext.Provider value={contextValue}>{children}</SourcesContext.Provider>;
}
