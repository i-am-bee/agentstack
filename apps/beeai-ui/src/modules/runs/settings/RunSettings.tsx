/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SettingsAdjust } from '@carbon/icons-react';

import { useAgentRun } from '../contexts/agent-run';
import { RunDialogButton } from './RunDialogButton';
import { RunSettingsForm } from './RunSettingsForm';
import type { RunSettingsDialogReturn } from './useRunSettingsDialog';

interface Props {
  dialog: RunSettingsDialogReturn;
  iconOnly?: boolean;
}

export function RunSettings({ dialog, iconOnly }: Props) {
  const { settingsRender } = useAgentRun();

  if (!settingsRender?.fields.length) {
    return null;
  }

  return (
    <RunDialogButton dialog={dialog} label="Settings" icon={SettingsAdjust} iconOnly={iconOnly}>
      <RunSettingsForm settingsRender={settingsRender} />
    </RunDialogButton>
  );
}
