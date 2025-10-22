/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cube } from '@carbon/icons-react';
import isEmpty from 'lodash/isEmpty';

import { useAgentDemands } from '../contexts/agent-demands';
import { useAgentRun } from '../contexts/agent-run';
import { ModelProviders } from './ModelProviders';
import { RunDialogButton } from './RunDialogButton';
import type { RunSettingsDialogReturn } from './useRunSettingsDialog';

interface Props {
  dialog: RunSettingsDialogReturn;
  iconOnly?: boolean;
}

export function RunModels({ dialog, iconOnly = true }: Props) {
  const { hasMessages } = useAgentRun();
  const { matchedLLMProviders, matchedEmbeddingProviders } = useAgentDemands();

  if (isEmpty(matchedLLMProviders) && isEmpty(matchedEmbeddingProviders)) {
    return null;
  }

  return (
    <RunDialogButton dialog={dialog} label="Models" icon={Cube} useButtonReference={iconOnly && !hasMessages}>
      <ModelProviders />
    </RunDialogButton>
  );
}
