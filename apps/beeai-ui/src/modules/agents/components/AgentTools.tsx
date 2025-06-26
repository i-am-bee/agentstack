/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';

import type { Agent } from '../api/types';
import { getAgentUiMetadata } from '../utils';
import classes from './AgentTools.module.scss';

interface Props {
  agent: Agent;
}

export function AgentTools({ agent }: Props) {
  const { tools } = getAgentUiMetadata(agent);

  return (
    <div className={classes.root}>
      {tools?.length ? (
        <ul className={classes.list}>
          {tools.map(({ name, description }, idx) => (
            <li key={idx} className={classes.item}>
              <span className={classes.header}>
                {/* <span className={classes.icon}></span> */}

                <span className={classes.name}>{name}</span>
              </span>
              {description && (
                <LineClampText className={classes.description} buttonClassName={classes.viewMore} lines={3}>
                  {description}
                </LineClampText>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className={classes.empty}>This agent does not have any tools</p>
      )}
    </div>
  );
}
