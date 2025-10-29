/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { IbmWatsonDiscovery, PartlyCloudy, Tools } from '@carbon/icons-react';

import Wikipedia from '#svgs/Wikipedia.svg';

import type { Tool } from '../api/types';
import classes from './ToolIcon.module.scss';

interface Props {
  name: Tool['name'];
}

export function ToolIcon({ name }: Props) {
  const Icon = ICONS_MAP[name as keyof typeof ICONS_MAP] ?? Tools;

  return (
    <span className={classes.root}>
      <Icon />
    </span>
  );
}

const ICONS_MAP = {
  search: IbmWatsonDiscovery,
  wikipedia: Wikipedia,
  weather: PartlyCloudy,
};
