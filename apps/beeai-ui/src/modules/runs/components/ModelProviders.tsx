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
  const {
    matchedLLMProviders,
    selectedLLMProviders,
    selectLLMProvider,
    matchedEmbeddingProviders,
    selectedEmbeddingProviders,
    selectEmbeddingProvider,
  } = usePlatformContext();

  const htmlId = useId();

  const llmProviderList = useMemo(
    () => Object.entries(matchedLLMProviders || {}).map(([key, items]) => ({ key, items })),
    [matchedLLMProviders],
  );

  const embeddingProviderList = useMemo(
    () => Object.entries(matchedEmbeddingProviders || {}).map(([key, items]) => ({ key, items })),
    [matchedEmbeddingProviders],
  );

  return (
    <div className={classes.root}>
      {llmProviderList.map(({ key, items }) => (
        <div key={key} className={classes.item}>
          <Tooltip content="Model" asChild size="sm">
            <ModelAlt size={20} className={classes.icon} />
          </Tooltip>
          <Select
            size="sm"
            id={`${htmlId}:${key}`}
            labelText={`${key} LLM`}
            hideLabel={llmProviderList.length === 1}
            inline
            value={selectedLLMProviders[key] || ''}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              selectLLMProvider(key, event.target.value);
            }}
          >
            {items.map((item) => (
              <SelectItem key={item} text={item} value={item} />
            ))}
          </Select>
        </div>
      ))}
      {embeddingProviderList.map(({ key, items }) => (
        <div key={key} className={classes.item}>
          <Tooltip content="Model" asChild size="sm">
            <ModelAlt size={20} className={classes.icon} />
          </Tooltip>
          <Select
            size="sm"
            id={`${htmlId}:${key}`}
            labelText={`${key} Embedding`}
            hideLabel={embeddingProviderList.length === 1}
            inline
            value={selectedEmbeddingProviders[key] || ''}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              selectEmbeddingProvider(key, event.target.value);
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
