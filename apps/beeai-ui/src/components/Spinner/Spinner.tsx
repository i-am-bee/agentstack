/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { lazy } from 'react';

import SpinnerAnimation from './BouncingDotsAnimation.json';
import classes from './Spinner.module.scss';

// Needs to be lazily loaded due to an error when used with Next.js https://github.com/Gamote/lottie-react/issues/123
const Lottie = lazy(() => import('lottie-react'));

interface Props {
  size?: 'sm' | 'md';
  center?: boolean;
}

export function Spinner({ size = 'md', center }: Props) {
  return (
    <div className={clsx(classes.root, classes[`size-${size}`], { [classes.center]: center })}>
      <Lottie className={classes.content} animationData={SpinnerAnimation} loop />
    </div>
  );
}
