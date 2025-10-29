/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled, Password } from '@carbon/icons-react';
import { OperationalTag, Tag } from '@carbon/react';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import classes from './SecretTag.module.scss';

interface Props {
  secret: AgentSecret;
  size?: 'md' | 'lg';
  onClick?: () => void;
}

export function SecretTag({ secret, size = 'lg', onClick }: Props) {
  const { isReady } = secret;

  if (isReady) {
    return (
      <Tag className={classes.root} renderIcon={CheckmarkFilled} onClick={onClick} size={size} type="green" as="button">
        Ready to use
      </Tag>
    );
  }

  return (
    <OperationalTag className={classes.root} size={size} renderIcon={Password} text="Add secret" onClick={onClick} />
  );
}
