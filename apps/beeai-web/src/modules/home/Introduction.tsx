/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import { GitHubButton } from './components/GitHubButton';
import { LogoBeeAI } from './components/LogoBeeAI';
import classes from './Introduction.module.scss';

export function Introduction() {
  return (
    <LayoutContainer>
      <section className={classes.root}>
        <div className={classes.headline}>
          <h1>
            <LogoBeeAI /> <br />
            control and agency without compromise
          </h1>
          <GitHubButton />
        </div>
      </section>
    </LayoutContainer>
  );
}
