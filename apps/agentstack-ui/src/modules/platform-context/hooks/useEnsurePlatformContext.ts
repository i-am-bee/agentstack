/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';

import { usePlatformContext } from '../contexts';

export function useEnsurePlatformContext(agent?: Agent) {
  const isRunning = useRef(false);

  const { contextId, createContext } = usePlatformContext();

  useEffect(() => {
    if (isRunning.current || !agent) {
      return;
    }
    isRunning.current = true;

    const ensureContext = async () => {
      if (!contextId) {
        await createContext({});
      }
    };

    ensureContext().finally(() => {
      isRunning.current = false;
    });
  }, [agent, contextId, createContext]);
}
