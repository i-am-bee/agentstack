/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { ElementType, PropsWithChildren } from 'react';

import classes from './TwoColumnGrid.module.scss';

interface Props {
  as?: ElementType;
  className?: string;
}

export function TwoColumnGrid({ as, className, children }: PropsWithChildren<Props>) {
  const Component = as || 'div';

  return <Component className={clsx(classes.root, className)}>{children}</Component>;
}
