/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { LayoutContainer } from '@/layouts/LayoutContainer';

import { LogoBeeAI } from './components/LogoBeeAI';
import { PrimaryCTALink } from './components/PrimaryCTALink';
import classes from './Introduction.module.scss';

export function Introduction() {
  return (
    <LayoutContainer>
      <section className={classes.root}>
        <div className={classes.headline}>
          <h1>
            <LogoBeeAI />
            <br />
            Ecosystem
          </h1>

          <p>A Series of Linux Foundation projects advancing AI agents</p>
        </div>

        <PrimaryCTALink />
      </section>
    </LayoutContainer>
  );
}
