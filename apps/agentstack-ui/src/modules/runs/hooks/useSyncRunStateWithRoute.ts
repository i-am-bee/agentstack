/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { routes } from '#utils/router.ts';

import { useAgentRun } from '../contexts/agent-run';

/**
 * Hook to keep the run state in sync with the route.
 * Since there is no way to do the shallow update to a new route with app router, and we need to use
 * history.pushState to avoid remounting the component, we also need to manually handle the URL changes
 * on shallow navigation (browser history, same route push) and update the run state accordingly.
 */
export function useSyncRunStateWithRoute() {
  const { agent, clear, hasMessages } = useAgentRun();

  const { contextId: contextIdUrl } = useParamsFromUrl();
  const { contextId, resetContext } = usePlatformContext();
  const router = useRouter();

  // Clear run if landing page is loaded (contextId not present in the url),
  // because Next.js thinks it's on the same page when previous context url
  // was updated via history.pushState, which we need to do for newly created contexts.
  useEffect(() => {
    if (hasMessages && !contextIdUrl) {
      clear();
      resetContext();
    }
  }, [clear, contextIdUrl, hasMessages, resetContext]);

  // Reload the context history route if contextId in the URL does not match
  // the one in the platform-context (happens on browser navigation)
  useEffect(() => {
    if (contextId && contextIdUrl && contextIdUrl !== contextId) {
      router.replace(routes.agentRun({ providerId: agent.provider.id, contextId: contextIdUrl }));
    }
  }, [agent.provider.id, contextId, contextIdUrl, router]);

  // We have no way to detect the history navigation reliably, so we refresh the route
  // on each contextId change to refetch the context data.
  useEffect(() => {
    if (contextId) {
      router.refresh();
    }
  }, [contextId, router]);
}
