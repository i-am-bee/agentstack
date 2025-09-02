/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ModelAlt } from '@carbon/icons-react';
import { Dropdown } from '@carbon/react';
import { useId, useMemo } from 'react';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';

import classes from './ModelProviders.module.scss';

export function ModelProviders() {
  const { matchedProviders, selectedProviders, selectProvider } = usePlatformContext();

  const htmlId = useId();

  const providersList = useMemo(
    () => Object.entries(matchedProviders || {}).map(([key, items]) => ({ key, items })),
    [matchedProviders],
  );

  return (
    <div className={classes.root}>
      {providersList.map(({ key, items }) => (
        <div key={key} className={classes.item}>
          <Tooltip content="Model" asChild size="sm">
            <ModelAlt size={20} className={classes.icon} />
          </Tooltip>
          <Dropdown
            size="sm"
            items={items}
            id={`${htmlId}:${key}`}
            label=""
            titleText={key}
            type="inline"
            selectedItem={selectedProviders[key]}
            hideLabel={items.length === 1}
            onChange={({ selectedItem }: { selectedItem: string | null }) =>
              selectedItem && selectProvider(key, selectedItem)
            }
          />
        </div>
      ))}
    </div>
  );
}
