/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { LayoutContainer } from '@/layouts/LayoutContainer';
import BeeLogo from '@/svgs/LogoBeeAI.svg';

import { GitHubButton } from './GitHubButton';
import classes from './Introduction.module.scss';

export function Introduction() {
  return (
    <LayoutContainer>
      <div className={classes.root}>
        <div className={classes.logo}>
          <BeeLogo />
        </div>
        <h1>Enterprise AI Agent Development, Simplified</h1>
        <GitHubButton />
      </div>
    </LayoutContainer>
  );
}
