/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled } from '@carbon/icons-react';
import { Tag } from '@carbon/react';
import { useMemo } from 'react';

import { useAgentSettings } from '#modules/runs/contexts/agent-settings/index.ts';

import classes from './AgentSecrets.module.scss';

export function AgentSecrets() {
  const { requestedSecrets } = useAgentSettings();

  const secrets = useMemo(() => {
    if (!requestedSecrets) {
      return [];
    }

    return Object.entries(requestedSecrets).map(([key, secret]) => {
      return { key, ...secret };
    });
  }, [requestedSecrets]);

  return (
    <div className={classes.root}>
      {secrets.length ? (
        <ul className={classes.list}>
          {secrets.map((secret, idx) => (
            <li key={idx}>
              <div className={classes.title}>{secret.name}</div>
              <p>{secret.description}</p>
              {secret.isReady ? (
                <Tag type="green" className={classes.ready}>
                  <CheckmarkFilled /> Ready to use
                </Tag>
              ) : (
                <Tag className={classes.pending}>Required</Tag>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className={classes.empty}>This agent does not have any secrets</p>
      )}
    </div>
  );
}
