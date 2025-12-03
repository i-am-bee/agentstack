/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

export const MermaidContext = createContext<MermaidContextValue | null>(null);

export interface MermaidContextValue {
  diagrams: Map<number, string>;
  setDiagram: (index: number, svg: string) => void;
}
