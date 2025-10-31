/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { AppName } from '#components/AppName/AppName.tsx';
import { AppHeader } from '#components/layouts/AppHeader.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';

import { AgentDetailButton } from './AgentDetailButton';
import classes from './AgentHeader.module.scss';
import { AgentShareButton } from './AgentShareButton';

export function AgentHeader() {
  const { providerId } = useParamsFromUrl();
  const { data: agent } = useAgent({ providerId });

  return (
    <AppHeader>
      <div className={classes.root}>
        <AppName />

        {agent && (
          <>
            <p className={classes.agentName}>{agent.name}</p>

            <div className={classes.buttons}>
              <AgentShareButton agent={agent} />

              <AgentDetailButton />
            </div>
          </>
        )}
      </div>
    </AppHeader>
  );
}
