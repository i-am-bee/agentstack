/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSecret } from '../contexts/agent-secrets/types';
import { SecretCard } from './SecretCard';
import classes from './SecretCardsList.module.scss';

interface Props {
  secrets: AgentSecret[];
  updateSecret: (key: string, value: string) => void;
  onCloseAddModal?: () => void;
  onOpenAddModal?: () => void;
}

export function SecretCardsList({ secrets, updateSecret, ...props }: Props) {
  return (
    <ul className={classes.root}>
      {secrets.map((secret) => (
        <li key={secret.key}>
          <SecretCard secret={secret} updateSecret={updateSecret} {...props} />
        </li>
      ))}
    </ul>
  );
}
