/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { AppName } from '#components/AppName/AppName.tsx';
import { AppHeader } from '#components/layouts/AppHeader.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';

import { AgentAuthor } from './AgentAuthor';
import { AgentDetailButton } from './AgentDetailButton';
import classes from './AgentHeader.module.scss';
import { AgentShareButton } from './AgentShareButton';

export function AgentHeader() {
  const { providerId } = useParamsFromUrl();
  const { data: agent } = useAgent({ providerId });
  const author = agent?.ui.author;

  return (
    <AppHeader>
      <div className={classes.root}>
        <AppName />

        {agent && (
          <>
            <div className={classes.header}>
              {author && <AgentAuthor author={author} />}

              <p className={classes.agentName}>{agent.name}</p>
            </div>

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
