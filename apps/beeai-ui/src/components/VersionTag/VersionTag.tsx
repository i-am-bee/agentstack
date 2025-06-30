/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tag } from '@carbon/react';
import type { ComponentProps, PropsWithChildren } from 'react';

import classes from './VersionTag.module.scss';

type Props = ComponentProps<typeof Tag>;

export function VersionTag({ children, ...props }: PropsWithChildren<Props>) {
  return (
    <Tag type="green" className={classes.root} {...props}>
      {children}
    </Tag>
  );
}
