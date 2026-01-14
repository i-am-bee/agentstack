/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cube, WarningFilled } from '@carbon/icons-react';
import isEmpty from 'lodash/isEmpty';

import { useAgentDemands } from '../contexts/agent-demands';
import { useAgentRun } from '../contexts/agent-run';
import { ModelProviders } from './ModelProviders';
import { RunDialogButton } from './RunDialogButton';
import classes from './RunModels.module.scss';
import type { RunSettingsDialogReturn } from './useRunSettingsDialog';

interface Props {
  dialog: RunSettingsDialogReturn;
  iconOnly?: boolean;
}

export function RunModels({ dialog, iconOnly = true }: Props) {
  const { hasMessages } = useAgentRun();
  const { llmProviders, embeddingProviders } = useAgentDemands();

  if (!llmProviders.isEnabled && !embeddingProviders.isEnabled) {
    return null;
  }

  if (llmProviders.isLoading || embeddingProviders.isLoading) {
    return <RunDialogButton.Loading description="Loading models" />;
  }

  const hasLLMMatched = !isEmpty(llmProviders.matched);
  const hasEmbeddingMatched = !isEmpty(embeddingProviders.matched);
  const hasUnmatchedDemands =
    (llmProviders.isEnabled && !hasLLMMatched) || (embeddingProviders.isEnabled && !hasEmbeddingMatched);

  return (
    <div className={classes.root}>
      <RunDialogButton
        dialog={dialog}
        label={
          hasUnmatchedDemands ? 'A required model is not available, so the agent might not work properly.' : 'Models'
        }
        icon={Cube}
        useButtonReference={iconOnly && !hasMessages}
        iconOnly={iconOnly}
      >
        <ModelProviders />
      </RunDialogButton>
      {hasUnmatchedDemands && (
        <span className={classes.warning}>
          <WarningFilled size={14} />
        </span>
      )}
    </div>
  );
}
