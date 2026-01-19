/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import type { Mermaid } from 'mermaid';
import { createContext } from 'react';

export interface MermaidContextValue {
  diagrams: Map<number, string | Error>;
  setDiagram: (index: number, value: string | Error) => void;
  mermaidApi: Mermaid | null;
  setMermaidApi: (api: Mermaid) => void;
}

export const MermaidContext = createContext<MermaidContextValue | null>(null);
