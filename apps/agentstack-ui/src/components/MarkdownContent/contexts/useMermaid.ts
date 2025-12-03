/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { useContext } from 'react';

import { MermaidContext } from './mermaid-context';

export function useMermaid() {
  const context = useContext(MermaidContext);

  if (!context) {
    throw new Error('useMermaid must be used within MermaidProvider');
  }

  return context;
}
