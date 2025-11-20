/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { UIArtifactPart } from '#modules/messages/types.ts';

export const CanvasContext = createContext<CanvasContextValue | null>(null);

export interface CanvasContextValue {
  artifacts?: UIArtifactPart[] | null;
  activeArtifact: UIArtifactPart | null;
  setActiveArtifactId: (id: string | null) => void;
  getArtifact: (id: string) => UIArtifactPart | undefined;
}
