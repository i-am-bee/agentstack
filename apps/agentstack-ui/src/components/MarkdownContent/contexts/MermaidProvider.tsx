/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import type { MermaidContextValue } from './mermaid-context';
import { MermaidContext } from './mermaid-context';

export function MermaidProvider({ children }: PropsWithChildren) {
  const [diagrams, setDiagrams] = useState<Map<number, string | Error>>(new Map());

  const setDiagram = useCallback((index: number, svg: string) => {
    setDiagrams((prev) => {
      const newMap = new Map(prev);
      newMap.set(index, svg);
      return newMap;
    });
  }, []);

  const value = useMemo<MermaidContextValue>(
    () => ({
      diagrams,
      setDiagram,
    }),
    [diagrams, setDiagram],
  );

  return <MermaidContext.Provider value={value}>{children}</MermaidContext.Provider>;
}
