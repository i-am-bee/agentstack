/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';

import { oauthMessageSchema } from '#api/a2a/extensions/services/oauth-provider.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

interface Props {
  onSuccess: (taskId: TaskId, redirectUri: string) => Promise<void>;
}

export function useStartOAuth({ onSuccess }: Props) {
  const startAuth = useCallback(
    (url: string, taskId: TaskId) => {
      const popup = window.open(url);
      if (!popup) {
        throw new Error('Failed to open popup');
      }
      popup.focus();

      // Check the status of opened window nad remove message listener, when it was closed
      const timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer);
          window.removeEventListener('message', handler);
        }
      }, 500);

      async function handler(message: unknown) {
        const { success, data: parsedMessage } = oauthMessageSchema.safeParse(message);
        if (!success) {
          return;
        }

        if (popup) {
          window.removeEventListener('message', handler);
          popup.close();

          await onSuccess(taskId, parsedMessage.data.redirect_uri);
        }
      }

      window.addEventListener('message', handler);
    },
    [onSuccess],
  );

  return { startAuth };
}
