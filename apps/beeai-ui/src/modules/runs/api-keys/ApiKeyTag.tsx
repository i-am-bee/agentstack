/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CheckmarkFilled, Password } from '@carbon/icons-react';
import { OperationalTag, Tag } from '@carbon/react';

import classes from './ApiKeyTag.module.scss';

interface Props {
  size?: 'md' | 'lg';
  onClick?: () => void;
}

export function ApiKeyTag({ size = 'lg', onClick }: Props) {
  const isReady = true;

  if (isReady) {
    return (
      <Tag size={size} renderIcon={CheckmarkFilled} type="green">
        Ready to use
      </Tag>
    );
  }

  return (
    <OperationalTag className={classes.root} size={size} renderIcon={Password} text="Add API key" onClick={onClick} />
  );
}
