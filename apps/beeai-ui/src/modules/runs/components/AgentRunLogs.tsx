/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import clsx from 'clsx';
import { useState } from 'react';

import { useAutoScroll } from '#hooks/useAutoScroll.ts';

import type { RunLog } from '../types';
import { formatLog } from '../utils';
import { AgentRunLogItem } from './AgentRunLogItem';
import classes from './AgentRunLogs.module.scss';

interface Props {
  logs: RunLog[];
  toggleable?: boolean;
}

export function AgentRunLogs({ logs, toggleable }: Props) {
  const { ref: autoScrollRef } = useAutoScroll([logs.length]);
  const [isExpanded, setIsExpanded] = useState(false);

  return logs.length > 0 ? (
    <div className={classes.root}>
      {toggleable && (
        <button
          type="button"
          className={clsx(classes.toggle, { [classes.isExpanded]: isExpanded })}
          onClick={() => setIsExpanded((expanded) => !expanded)}
        >
          <span>How did I get this result?</span>

          <ChevronDown />
        </button>
      )}

      {(!toggleable || (toggleable && isExpanded)) && (
        <ul>
          {logs.map((log, idx) => (
            <li key={idx}>
              <AgentRunLogItem>{formatLog(log)}</AgentRunLogItem>
            </li>
          ))}
        </ul>
      )}

      <div ref={autoScrollRef} className={classes.bottom} />
    </div>
  ) : null;
}
