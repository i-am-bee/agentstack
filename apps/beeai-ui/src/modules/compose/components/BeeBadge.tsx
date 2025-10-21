/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Tag } from '@carbon/react';
import type { ComponentProps } from 'react';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import Bee from '#svgs/bee.svg';
import { BEE_AI_FRAMEWORK_TAG } from '#utils/constants.ts';

import type { Agent } from '../../agents/api/types';
import classes from './BeeBadge.module.scss';

interface Props {
  agent: Agent;
  size?: ComponentProps<typeof Tag>['size'];
}

export function BeeBadge({ agent, size }: Props) {
  const { framework } = agent.ui;
  return (
    <>
      {framework === BEE_AI_FRAMEWORK_TAG && (
        <Tooltip content="Built by the BeeAI team" placement="top" asChild>
          <Tag type="green" renderIcon={Bee} size={size} className={classes.tag} />
        </Tooltip>
      )}
    </>
  );
}
