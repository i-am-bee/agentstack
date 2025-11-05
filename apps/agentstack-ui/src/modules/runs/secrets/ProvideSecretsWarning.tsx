/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Callout } from '@carbon/react';

import classes from './ProvideSecretsWarning.module.scss';

export function ProvideSecretsWarning() {
  return (
    <Callout
      title="Provide your API key"
      subtitle="To effectively use this agent, please provide your API keys. You can skip this step for now and provide them later in the chat."
      lowContrast
      kind="warning"
      actionButtonLabel="Add secrets"
      onActionButtonClick={() => {}}
      className={classes.root}
    />
  );
}
