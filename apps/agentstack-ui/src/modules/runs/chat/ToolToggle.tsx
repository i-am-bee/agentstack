/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ToggleProps } from '@carbon/react';
import { SkeletonIcon, SkeletonText, Toggle, ToggleSkeleton } from '@carbon/react';

import type { Tool } from '#modules/tools/api/types.ts';
import { ToolIcon } from '#modules/tools/components/ToolIcon.tsx';
import { ToolName } from '#modules/tools/components/ToolName.tsx';

import classes from './ToolToggle.module.scss';

interface Props extends Pick<ToggleProps, 'toggled' | 'onToggle'> {
  tool: Tool;
}
export function ToolToggle({ tool, ...props }: Props) {
  const { name } = tool;

  return (
    <div className={classes.root}>
      <ToolIcon name={name} />

      <h3 className={classes.heading}>
        <ToolName name={name} />
      </h3>

      <Toggle {...props} id={name} className={classes.toggle} size="sm" />
    </div>
  );
}

ToolToggle.Skeleton = function ToolToggleSkeleton() {
  return (
    <div className={classes.root}>
      <span className={classes.icon}>
        <SkeletonIcon />
      </span>

      <SkeletonText className={classes.heading} />

      <ToggleSkeleton className={classes.toggle} />
    </div>
  );
};
