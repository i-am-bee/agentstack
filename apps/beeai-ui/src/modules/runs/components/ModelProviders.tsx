/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ModelAlt } from '@carbon/icons-react';
import { Select, SelectItem } from '@carbon/react';
import type { ChangeEvent } from 'react';
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
          <Select
            size="sm"
            id={`${htmlId}:${key}`}
            labelText={key}
            hideLabel={providersList.length === 1}
            inline
            value={selectedProviders[key] || ''}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              selectProvider(key, event.target.value);
            }}
          >
            {items.map((item) => (
              <SelectItem key={item} text={item} value={item} />
            ))}
          </Select>
        </div>
      ))}
    </div>
  );
}
