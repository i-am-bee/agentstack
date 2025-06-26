/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { lazy, useState } from 'react';

import Logo from '#svgs/LogoBeeAI.svg';

import animationData from './LogoBeeAI.json';
import classes from './LogoBeeAI.module.scss';

// Needs to be lazily loaded due to an error when used with Next.js https://github.com/Gamote/lottie-react/issues/123
const Lottie = lazy(() => import('lottie-react'));

export function LogoBeeAI() {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className={clsx(classes.container, { [classes.loaded]: loaded })}>
      <div className={classes.placeholder}>
        <Logo />
      </div>

      <Lottie
        className={classes.animation}
        animationData={animationData}
        loop={false}
        onDOMLoaded={() => {
          setLoaded(true);
        }}
      />
    </div>
  );
}
