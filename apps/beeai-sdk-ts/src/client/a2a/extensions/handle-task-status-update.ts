/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { SecretDemands } from './services/secrets';
import { secretsMessageExtension } from './services/secrets';
import { extractUiExtensionData } from './utils';
import { formMessageExtension, FormDemands } from './ui/form';

const secretsMessageExtensionExtractor = extractUiExtensionData(secretsMessageExtension);
const formMessageExtensionExtractor = extractUiExtensionData(formMessageExtension);

export enum TaskStatusUpdateType {
  SecretRequired = 'secret-required',
  FormRequired = 'form-required',
}

interface SecretRequiredResult {
  type: TaskStatusUpdateType.SecretRequired;
  demands: SecretDemands;
}

interface FormRequiredResult {
  type: TaskStatusUpdateType.FormRequired;
  form: FormDemands;
}

type TaskStatusUpdateResult = SecretRequiredResult | FormRequiredResult;

export const handleTaskStatusUpdate = (event: TaskStatusUpdateEvent): TaskStatusUpdateResult[] => {
  const results: TaskStatusUpdateResult[] = [];

  if (event.status.state === 'auth-required') {
    const secretRequired = secretsMessageExtensionExtractor(event.status.message?.metadata);

    if (secretRequired) {
      results.push({
        type: TaskStatusUpdateType.SecretRequired,
        demands: secretRequired,
      });
    }
  } else if (event.status.state === 'input-required') {
    const formRequired = formMessageExtensionExtractor(event.status.message?.metadata);
    if (formRequired) {
      results.push({
        type: TaskStatusUpdateType.FormRequired,
        form: formRequired,
      });
    }
  }

  // TODO: OAuth

  return results;
};
