/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useMemo } from 'react';

import { useModal } from '#contexts/Modal/index.tsx';
import { useUpdateVariable } from '#modules/variables/api/mutations/useUpdateVariable.ts';

import type { AgentSecret } from '../contexts/agent-secrets/types';

export function useRevokeSecret({ onSuccess }: { onSuccess?: () => void } = {}) {
  const { openConfirmation } = useModal();
  const { mutate: updateVariable } = useUpdateVariable();

  const revokeSecret = useCallback(
    ({ key }: AgentSecret) =>
      openConfirmation({
        title: 'Revoke API Key',
        body: 'Are you sure you want to remove this API key?',
        danger: true,
        primaryButtonText: 'Remove',
        onSubmit: () => {
          updateVariable({ key, value: null });
          onSuccess?.();
        },
      }),
    [openConfirmation, updateVariable, onSuccess],
  );

  return useMemo(() => ({ revokeSecret }), [revokeSecret]);
}
