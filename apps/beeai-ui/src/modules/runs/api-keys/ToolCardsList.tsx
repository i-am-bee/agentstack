/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ToolCard } from './ToolCard';
import classes from './ToolCardsList.module.scss';

export function ToolCardsList() {
  const items = [1, 2, 3];

  return (
    <ul className={classes.root}>
      {items.map((item) => (
        <li key={item}>
          <ToolCard />
        </li>
      ))}
    </ul>
  );
}
