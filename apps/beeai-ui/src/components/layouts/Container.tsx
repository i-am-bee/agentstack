/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import classes from './Container.module.scss';

interface Props {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xlg' | 'xxl' | 'max' | 'full';
  className?: string;
}

export function Container({ size = 'md', className, children }: PropsWithChildren<Props>) {
  return <div className={clsx(classes.root, className, { [classes[size]]: size })}>{children}</div>;
}
