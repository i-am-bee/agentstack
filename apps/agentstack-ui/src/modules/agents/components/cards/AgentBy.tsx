/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FC, PropsWithChildren, SVGProps } from 'react';

import classes from './AgentBy.module.scss';

interface Props extends PropsWithChildren {
  Icon: FC<SVGProps<SVGSVGElement>>;
}

export function AgentBy({ Icon, children }: Props) {
  return (
    <p className={classes.root}>
      <Icon className={classes.icon} />

      <span>{children}</span>
    </p>
  );
}
