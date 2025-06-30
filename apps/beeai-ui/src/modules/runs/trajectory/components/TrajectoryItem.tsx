/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { useState } from 'react';

import type { TrajectoryMetadata } from '#modules/runs/api/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './TrajectoryItem.module.scss';
import { TrajectoryItemContent } from './TrajectoryItemContent';

interface Props {
  trajectory: TrajectoryMetadata;
}

export function TrajectoryItem({ trajectory }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const { tool_name, message } = trajectory;

  const isToggleable = isNotNull(message);

  return (
    <div className={clsx(classes.root, { [classes.isOpen]: isOpen })}>
      <header className={classes.header}>
        {isToggleable && (
          <IconButton
            kind="ghost"
            size="sm"
            label={isOpen ? 'Collapse' : 'Expand'}
            wrapperClasses={classes.button}
            onClick={() => setIsOpen((state) => !state)}
          >
            <ChevronDown />
          </IconButton>
        )}

        {tool_name && (
          <h3 className={classes.name}>
            {/* <span className={classes.icon}>
            <Icon />
          </span> */}

            <span>{tool_name}</span>
          </h3>
        )}

        {message && <div className={classes.message}>{message}</div>}
      </header>

      {isToggleable && (
        <div className={classes.body}>
          <div className={classes.panel}>
            <TrajectoryItemContent trajectory={trajectory} />
          </div>
        </div>
      )}
    </div>
  );
}
