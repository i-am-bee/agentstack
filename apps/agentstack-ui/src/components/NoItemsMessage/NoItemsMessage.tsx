/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import classes from './NoItemsMessage.module.scss';

interface Props {
  message: string;
  className?: string;
}

export function NoItemsMessage({ message, className }: Props) {
  return <p className={clsx(classes.empty, className)}>{message}</p>;
}
