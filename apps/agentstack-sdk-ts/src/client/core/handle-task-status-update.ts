/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { oauthRequestExtension } from '../a2a/extensions/auth/oauth';
import { secretsRequestExtension } from '../a2a/extensions/auth/secrets';
import { approvalExtension } from '../a2a/extensions/interactions/approval';
import { formRequestExtension } from '../a2a/extensions/ui/form-request';
import type { TaskStatusUpdateEvent } from '../a2a/protocol/types';
import { extractUiExtensionData } from './extensions/extract';
import type { TaskStatusUpdateResult } from './extensions/types';
import { TaskStatusUpdateType } from './extensions/types';
import { extractTextFromMessage } from './utils/extract-text-from-message';

const secretsRequestExtensionExtractor = extractUiExtensionData(secretsRequestExtension);
const oauthRequestExtensionExtractor = extractUiExtensionData(oauthRequestExtension);
const formRequestExtensionExtractor = extractUiExtensionData(formRequestExtension);
const approvalExtensionExtractor = extractUiExtensionData(approvalExtension);

export const handleTaskStatusUpdate = (event: TaskStatusUpdateEvent): TaskStatusUpdateResult[] => {
  const results: TaskStatusUpdateResult[] = [];

  if (event.status.state === 'auth-required') {
    const secretRequired = secretsRequestExtensionExtractor(event.status.message?.metadata);
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
    const formRequired = formRequestExtensionExtractor(event.status.message?.metadata);
    const approvalRequired = approvalExtensionExtractor(event.status.message?.metadata);

    if (formRequired) {
      results.push({
        type: TaskStatusUpdateType.FormRequired,
        form: formRequired,
      });
    } else if (approvalRequired) {
      results.push({
        type: TaskStatusUpdateType.ApprovalRequired,
        request: approvalRequired,
      });
    } else {
      const text = extractTextFromMessage(event.status.message);
      if (text) {
        results.push({
          type: TaskStatusUpdateType.TextInputRequired,
          text,
        });
      }
    }
  }

  return results;
};
