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
    <>
      <LayoutContainer>
        <section className={classes.root}>
          <div className={classes.headline}>
            <h1>
              <LogoBeeAI /> the enterprise
              <br />
              AI agent development,
              <br />
              simplified.
            </h1>
            <GitHubButton />
          </div>
        </section>
      </LayoutContainer>
      <section className={classes.info}>
        <LayoutContainer asGrid>
          <div className={classes.infoContent}>
            <p>
              BeeAI provides two complementary open- source components for Enterprise Developers: a&nbsp;
              <a href="#framework">framework</a> for building reliable AI agents and a <a href="#platform">platform</a>{' '}
              for creating shareable interfaces.
            </p>
          </div>
        </LayoutContainer>
      </section>
    </>
  );
}
