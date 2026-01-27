/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useMergeRefs } from '@floating-ui/react';

import { RunModels } from '#modules/runs/settings/RunModels.tsx';
import { RunSettings } from '#modules/runs/settings/RunSettings.tsx';
import { useRunSettingsDialog } from '#modules/runs/settings/useRunSettingsDialog.ts';

import classes from './FormActionBar.module.scss';

interface Props {
  submitLabel: string;
  submitDisabled?: boolean;
  showSubmit?: boolean;
  showRunSettings?: boolean;
}

export function FormActionBar({ submitLabel, submitDisabled, showSubmit = true, showRunSettings }: Props) {
  const modelsDialog = useRunSettingsDialog({ blockOffset: 8 });
  const settingsDialog = useRunSettingsDialog({ blockOffset: 8 });
  const formRefs = useMergeRefs([modelsDialog.refs.setPositionReference, settingsDialog.refs.setPositionReference]);

  return (
    <div className={classes.root} ref={formRefs}>
      {showRunSettings && (
        <div className={classes.settings}>
          <RunSettings dialog={settingsDialog} iconOnly={false} />

          <RunModels dialog={modelsDialog} iconOnly={false} />
        </div>
      )}

      {showSubmit && (
        <div className={classes.buttons}>
          <Button type="submit" size="md" disabled={submitDisabled}>
            {submitLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
