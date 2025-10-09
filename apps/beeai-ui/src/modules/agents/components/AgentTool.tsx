/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';

import type { AgentTool } from '../api/types';
import classes from './AgentTool.module.scss';

interface Props {
  tool: AgentTool;
}

export function AgentTool({ tool }: Props) {
  const { name, description } = tool;

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        {/* <span className={classes.icon}></span> */}

        <p className={classes.name}>{name}</p>
      </div>

      {description && (
        <LineClampText className={classes.description} buttonClassName={classes.viewMore} lines={3}>
          {description}
        </LineClampText>
      )}
    </div>
  );
}
