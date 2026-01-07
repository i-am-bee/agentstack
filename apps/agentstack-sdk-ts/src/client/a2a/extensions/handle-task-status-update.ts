/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { FormRender } from './common/form';
import type { ApprovalRequest } from './interactions/approval';
import { approvalExtension } from './interactions/approval';
import type { SecretDemands } from './services/secrets';
import { secretsMessageExtension } from './services/secrets';
import { FormRequestExtension } from './ui/form-request';
import { oauthRequestExtension } from './ui/oauth';
import { extractUiExtensionData } from './utils';

const secretsMessageExtensionExtractor = extractUiExtensionData(secretsMessageExtension);
const oauthRequestExtensionExtractor = extractUiExtensionData(oauthRequestExtension);
const FormRequestExtensionExtractor = extractUiExtensionData(FormRequestExtension);
const approvalExtensionExtractor = extractUiExtensionData(approvalExtension);

export enum TaskStatusUpdateType {
  SecretRequired = 'secret-required',
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
  ApprovalRequired = 'approval-required',
}

export interface SecretRequiredResult {
  type: TaskStatusUpdateType.SecretRequired;
  demands: SecretDemands;
}

export interface FormRequiredResult {
  type: TaskStatusUpdateType.FormRequired;
  form: FormRender;
}

export interface OAuthRequiredResult {
  type: TaskStatusUpdateType.OAuthRequired;
  url: string;
}

export interface ApprovalRequiredResult {
  type: TaskStatusUpdateType.ApprovalRequired;
  request: ApprovalRequest;
}

export type TaskStatusUpdateResult =
  | SecretRequiredResult
  | FormRequiredResult
  | OAuthRequiredResult
  | ApprovalRequiredResult;

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
    const formRequired = FormRequestExtensionExtractor(event.status.message?.metadata);
    const approvalRequired = approvalExtensionExtractor(event.status.message?.metadata);

    if (formRequired) {
      results.push({
        type: TaskStatusUpdateType.FormRequired,
        form: formRequired,
      });
    }

    if (approvalRequired) {
      results.push({
        type: TaskStatusUpdateType.ApprovalRequired,
        request: approvalRequired,
      });
    }
  }

  return results;
};
