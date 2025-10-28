/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SettingsAdjust } from '@carbon/icons-react';

import { useAgentDemands } from '../contexts/agent-demands';
import { RunDialogButton } from './RunDialogButton';
import { RunSettingsForm } from './RunSettingsForm';
import type { RunSettingsDialogReturn } from './useRunSettingsDialog';

interface Props {
  dialog: RunSettingsDialogReturn;
  iconOnly?: boolean;
}

export function RunSettings({ dialog, iconOnly }: Props) {
  const { settingsDemands } = useAgentDemands();

  if (!settingsDemands?.fields.length) {
    return null;
  }

  return (
    <RunDialogButton dialog={dialog} label="Settings" icon={SettingsAdjust} iconOnly={iconOnly}>
      <RunSettingsForm settingsDemands={settingsDemands} />
    </RunDialogButton>
  );
}
