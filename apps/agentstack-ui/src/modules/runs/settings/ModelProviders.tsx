/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { RadioSelect } from '#components/RadioSelect/RadioSelect.tsx';

import { useAgentDemands } from '../contexts/agent-demands';
import classes from './ModelProviders.module.scss';

export function ModelProviders() {
  const { llmProviders, embeddingProviders } = useAgentDemands();

  const llmProviderList = Object.entries(llmProviders.matched || {}).map(([key, items]) => ({ key, items }));

  const embeddingProviderList = Object.entries(embeddingProviders.matched || {}).map(([key, items]) => ({
    key,
    items,
  }));

  return (
    <div className={classes.root}>
      {llmProviderList.map(({ key, items }) => (
        <RadioSelect
          key={key}
          name={key}
          label={llmProviderList.length == 1 ? 'LLM' : `LLM: ${key}`}
          value={llmProviders.selected[key]}
          options={items.map((item) => ({ label: item, value: item }))}
          onChange={(value) => llmProviders.select(key, value)}
        />
      ))}
      {embeddingProviderList.map(({ key, items }) => (
        <RadioSelect
          key={key}
          name={key}
          label={embeddingProviderList.length == 1 ? 'Embedding' : `Embedding: ${key}`}
          value={embeddingProviders.selected[key]}
          options={items.map((item) => ({ label: item, value: item }))}
          onChange={(value) => embeddingProviders.select(key, value)}
        />
      ))}
    </div>
  );
}
