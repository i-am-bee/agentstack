/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { RadioSelect } from '#components/RadioSelect/RadioSelect.tsx';

import { useAgentDemands } from '../contexts/agent-demands';
import classes from './ModelProviders.module.scss';

export function ModelProviders() {
  const {
    matchedLLMProviders,
    selectedLLMProviders,
    selectLLMProvider,
    matchedEmbeddingProviders,
    selectedEmbeddingProviders,
    selectEmbeddingProvider,
  } = useAgentDemands();

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
        <RadioSelect
          key={key}
          name={key}
          label={llmProviderList.length == 1 ? 'LLM' : `LLM: ${key}`}
          value={selectedLLMProviders[key]}
          options={items.map((item) => ({ label: item, value: item }))}
          onChange={(value) => {
            selectLLMProvider(key, value);
          }}
        />
      ))}
      {embeddingProviderList.map(({ key, items }) => (
        <RadioSelect
          key={key}
          name={key}
          label={embeddingProviderList.length == 1 ? 'Embedding' : `Embedding: ${key}`}
          value={selectedEmbeddingProviders[key]}
          options={items.map((item) => ({ label: item, value: item }))}
          onChange={(value) => {
            selectEmbeddingProvider(key, value);
          }}
        />
      ))}
    </div>
  );
}
