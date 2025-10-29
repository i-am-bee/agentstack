/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import classes from './BlogHero.module.scss';

export function BlogHero() {
  return (
    <div className={classes.root}>
      <h1 className={classes.heading}>BeeAI Blog</h1>
      <p className={classes.subheading}>
        Announcements and deep technical dives from the team building BeeAI.
        <br />
        Insights on open agent infrastructure, architecture, and engineering.
      </p>
    </div>
  );
}
