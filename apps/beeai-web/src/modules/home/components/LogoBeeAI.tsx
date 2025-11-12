/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import Lottie from 'lottie-react';
import { useState } from 'react';

import Logo from '../assets/LogoBeeAI.svg';
import animationData from './LogoBeeAI.json';
import classes from './LogoBeeAI.module.scss';

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
