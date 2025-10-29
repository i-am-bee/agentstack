/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Slot } from '@radix-ui/react-slot';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import classes from './Container.module.scss';

interface Props {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xlg' | 'xxl' | 'max' | 'full';
  asChild?: boolean;
  className?: string;
}

export function Container({ size = 'md', asChild, className, children }: PropsWithChildren<Props>) {
  const Comp = asChild ? Slot : 'div';

  return <Comp className={clsx(classes.root, className, { [classes[size]]: size })}>{children}</Comp>;
}
