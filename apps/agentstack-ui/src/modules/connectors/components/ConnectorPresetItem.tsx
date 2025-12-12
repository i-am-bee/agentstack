/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText } from '@carbon/react';

import type { ConnectorPreset } from '../api/types';
import classes from './ConnectorPresetItem.module.scss';
import { ConnectPresetButton } from './ConnectPresetButton';

interface Props {
  preset: ConnectorPreset;
}

export function ConnectorPresetItem({ preset }: Props) {
  const { url, metadata } = preset;
  const { name, description } = metadata ?? {};

  return (
    <div className={classes.root}>
      <h3 className={classes.name}>{name ?? url}</h3>

      {description && <p className={classes.description}>{description}</p>}

      <ConnectPresetButton preset={preset} className={classes.connectBtn} />
    </div>
  );
}

ConnectorPresetItem.Skeleton = function ConnectorPresetItemSkeleton() {
  return (
    <div className={classes.root}>
      <SkeletonText className={classes.name} width="50%" />

      <SkeletonText className={classes.description} />
    </div>
  );
};
