/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { useAgentSecrets } from '#modules/runs/contexts/agent-secrets/index.ts';
import { SecretCard } from '#modules/runs/secrets/SecretCard.tsx';

import classes from './AgentSecrets.module.scss';

export function AgentSecrets() {
  const { demandedSecrets } = useAgentSecrets();

  return (
    <div className={classes.root}>
      {demandedSecrets.length ? (
        <ul className={classes.list}>
          {demandedSecrets.map((secret) => (
            <li key={secret.key}>
              <SecretCard secret={secret} variant="inline" />
            </li>
          ))}
        </ul>
      ) : (
        <NoItemsMessage message="This agent does not have any secrets" />
      )}
    </div>
  );
}
