/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import Bee from '../../../public/bee.svg';
import LinuxFoundation from './assets/linux-foundation.svg';
import classes from './Highlights.module.scss';

export function Highlights() {
  return (
    <section className={classes.root}>
      <div className={classes.item}>
        <Bee />
        <p>
          BeeAI helps enterprise developers turn <strong>ideas into production-ready agents</strong> with{' '}
          <strong>shareable interfaces</strong> - no need to build orchestration or frontends from scratch.
        </p>
      </div>
      <div className={classes.item}>
        <LinuxFoundation />
        <p>
          Fully <strong>open source</strong> under Linux Foundation - join us to shape the future of AI agents.
        </p>
      </div>
    </section>
  );
}
