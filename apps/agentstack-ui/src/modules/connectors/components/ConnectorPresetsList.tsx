/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import { useListConnectorPresets } from '../api/queries/useListConnectorPresets';
import { ConnectorPresetItem } from './ConnectorPresetItem';
import classes from './ConnectorPresetsList.module.scss';

export function ConnectorPresetsList() {
  const { data: presets, isPending } = useListConnectorPresets();

  return (
    <ul className={classes.root}>
      {!isPending ? (
        presets?.items.map((preset) => (
          <li key={preset.url}>
            <ConnectorPresetItem preset={preset} />
          </li>
        ))
      ) : (
        <SkeletonItems
          count={3}
          render={(idx) => (
            <li key={idx}>
              <ConnectorPresetItem.Skeleton />
            </li>
          )}
        />
      )}
    </ul>
  );
}
