/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef } from 'react';

export function useRunViewKey(agentName: string, contextId: string | null) {
  const prevWasStringRef = useRef<boolean>(typeof contextId === 'string');

  const key = prevWasStringRef.current ? `${agentName}:${contextId ?? '__NULL__'}` : agentName;

  useEffect(() => {
    prevWasStringRef.current = typeof contextId === 'string';
  }, [contextId]);

  return key;
}
