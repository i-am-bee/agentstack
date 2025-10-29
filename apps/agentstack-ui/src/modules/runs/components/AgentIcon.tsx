/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import Bee from '#svgs/bee.svg';

import classes from './AgentIcon.module.scss';

interface Props {
  size?: 'md' | 'xl';
  inverted?: boolean;
}

export function AgentIcon({ size = 'md', inverted }: Props) {
  return (
    <span className={clsx(classes.root, classes[`size-${size}`], { [classes.inverted]: inverted })}>
      <Bee />
    </span>
  );
}
