/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { A2AClient } from '@a2a-js/sdk/client';
import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AgentClientContext } from './agent-client-context';

interface Props {
  agent: Agent;
}

export function AgentClientProvider({ agent, children }: PropsWithChildren<Props>) {
  const value = useMemo(() => {
    const client = new A2AClient(`/api/v1/a2a/${agent.provider.id}`);

    // HACK: the URL in the agent card is not using the nextjs proxy - we need to replace it
    // eslint-disable-next-line
    (client as unknown as any).agentCardPromise.then(() => {
      // eslint-disable-next-line
      (client as unknown as any).serviceEndpointUrl = `${getBaseUrl()}/api/v1/a2a/${agent.provider.id}/`;
    });
    return { client, agent };
  }, [agent]);

  return <AgentClientContext.Provider value={value}>{children}</AgentClientContext.Provider>;
}
