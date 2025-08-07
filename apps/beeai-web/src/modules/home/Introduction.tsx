/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import BeeCollage from './assets/bee-collage.svg';
import { GitHubButton } from './components/GitHubButton';
import { LogoBeeAI } from './components/LogoBeeAI';
import classes from './Introduction.module.scss';

export function Introduction() {
  return (
    <LayoutContainer>
      <div className={classes.root}>
        <div>
          <div className={classes.logo}>
            {/* <BeeLogo /> */}
            <LogoBeeAI />
          </div>
          <h1>
            Enterprise AI Agent
            <br />
            Development,
            <br />
            Simplified
          </h1>
          <GitHubButton />
        </div>
        <div className={classes.collage}>
          <BeeCollage />
        </div>
      </div>
    </LayoutContainer>
  );
}
