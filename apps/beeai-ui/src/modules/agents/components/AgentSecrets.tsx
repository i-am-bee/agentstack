/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { useAgentSecrets } from '#modules/runs/contexts/agent-secrets/index.ts';
import { SecretCard } from '#modules/runs/secrets/SecretCard.tsx';

import classes from './AgentSecrets.module.scss';

export function AgentSecrets() {
  const { secrets, updateSecret } = useAgentSecrets();

  return (
    <div className={classes.root}>
      {secrets.length ? (
        <ul className={classes.list}>
          {secrets.map((secret) => (
            <li key={secret.key}>
              <SecretCard secret={secret} updateSecret={updateSecret} variant="inline" />
            </li>
          ))}
        </ul>
      ) : (
        <NoItemsMessage message="This agent does not have any secrets" />
      )}
    </div>
  );
}
