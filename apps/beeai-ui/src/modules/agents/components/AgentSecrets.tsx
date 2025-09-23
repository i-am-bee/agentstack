/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useModal } from '#contexts/Modal/index.tsx';
import { useAgentSecrets } from '#modules/runs/contexts/agent-secrets/index.ts';
import { SecretsAddModal } from '#modules/runs/secrets/SecretsAddModal.tsx';
import { SecretTag } from '#modules/runs/secrets/SecretTag.tsx';

import classes from './AgentSecrets.module.scss';

export function AgentSecrets() {
  const { openModal } = useModal();

  const { secrets, updateSecret } = useAgentSecrets();

  return (
    <div className={classes.root}>
      {secrets.length ? (
        <ul className={classes.list}>
          {secrets.map((secret, idx) => (
            <li key={idx}>
              <div className={classes.title}>{secret.name}</div>
              <p>{secret.description}</p>

              <SecretTag
                secret={secret}
                size="md"
                onClick={() =>
                  openModal((props) => <SecretsAddModal {...props} secret={secret} updateSecret={updateSecret} />)
                }
              />
            </li>
          ))}
        </ul>
      ) : (
        <p className={classes.empty}>This agent does not have any secrets</p>
      )}
    </div>
  );
}
