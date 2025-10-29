/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import classes from './BlogHero.module.scss';

export function BlogHero() {
  return (
    <div className={classes.root}>
      <h1 className={classes.heading}>
        Enterprise
        <br />
        AI agent
        <br />
        Framework
      </h1>
    </div>
  );
}
