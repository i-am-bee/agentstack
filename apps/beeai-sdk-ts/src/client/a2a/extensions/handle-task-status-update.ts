/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { SecretDemands } from './services/secrets';
import { secretsMessageExtension } from './services/secrets';
import type { FormDemands } from './ui/form';
import { formMessageExtension } from './ui/form';
import { oauthRequestExtension } from './ui/oauth';
import { extractUiExtensionData } from './utils';

const secretsMessageExtensionExtractor = extractUiExtensionData(secretsMessageExtension);
const formMessageExtensionExtractor = extractUiExtensionData(formMessageExtension);
const oauthRequestExtensionExtractor = extractUiExtensionData(oauthRequestExtension);

export enum TaskStatusUpdateType {
  SecretRequired = 'secret-required',
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
}

export interface SecretRequiredResult {
  type: TaskStatusUpdateType.SecretRequired;
  demands: SecretDemands;
}

export interface FormRequiredResult {
  type: TaskStatusUpdateType.FormRequired;
  form: FormDemands;
}

export interface OAuthRequiredResult {
  type: TaskStatusUpdateType.OAuthRequired;
  url: string;
}

export type TaskStatusUpdateResult = SecretRequiredResult | FormRequiredResult | OAuthRequiredResult;

export const handleTaskStatusUpdate = (event: TaskStatusUpdateEvent): TaskStatusUpdateResult[] => {
  const results: TaskStatusUpdateResult[] = [];

  if (event.status.state === 'auth-required') {
    const secretRequired = secretsMessageExtensionExtractor(event.status.message?.metadata);
    const oauthRequired = oauthRequestExtensionExtractor(event.status.message?.metadata);

    if (oauthRequired) {
      results.push({
        type: TaskStatusUpdateType.OAuthRequired,
        url: oauthRequired.authorization_endpoint_url,
      });
    }

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

  return results;
};
