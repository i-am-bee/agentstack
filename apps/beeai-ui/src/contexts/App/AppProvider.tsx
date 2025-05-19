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

import type { PropsWithChildren, RefObject } from 'react';
import { useMemo, useRef, useState } from 'react';
import { useOnClickOutside } from 'usehooks-ts';

import { isNotNull } from '#utils/helpers.ts';

import { AppContext } from './app-context';

export function AppProvider({ children }: PropsWithChildren) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [agentDetailOpen, setAgentDetailOpen] = useState(false);
  const [closeOnClickOutside, setCloseOnClickOutside] = useState(false);
  const navigationPanelRef = useRef<HTMLElement>(null);
  const navigationToggleRef = useRef<HTMLButtonElement>(null);

  const clickOutsideRefs = useMemo(
    () =>
      [
        navigationPanelRef.current ? navigationPanelRef : null,
        navigationToggleRef.current ? navigationToggleRef : null,
      ].filter(isNotNull) as RefObject<HTMLElement>[],
    [],
  );

  useOnClickOutside(clickOutsideRefs, () => {
    if (closeOnClickOutside) {
      setNavigationOpen(false);
    }
  });

  const contextValue = useMemo(
    () => ({ navigationOpen, agentDetailOpen, setNavigationOpen, setAgentDetailOpen }),
    [navigationOpen, agentDetailOpen],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}
