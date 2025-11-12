/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import classes from './Spinner.module.scss';

interface Props {
  center?: boolean;
}

export function Spinner({ center }: Props) {
  return (
    <span className={clsx(classes.root, { [classes.center]: center })}>
      <span className={clsx(classes.dot, classes.left)} />
      <span className={clsx(classes.dot, classes.middle)} />
      <span className={clsx(classes.dot, classes.right)} />
    </span>
  );
}
