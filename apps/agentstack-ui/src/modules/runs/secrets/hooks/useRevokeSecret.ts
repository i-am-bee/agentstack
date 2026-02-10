/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useModal } from '#contexts/Modal/index.tsx';
import { useUpdateVariable } from '#modules/variables/api/mutations/useUpdateVariable.ts';

import type { AgentSecret } from '../../contexts/agent-secrets/types';

export function useRevokeSecret({ onSuccess }: { onSuccess?: () => void } = {}) {
  const { openConfirmation } = useModal();
  const { mutate: updateVariable } = useUpdateVariable({ onSuccess });

  const revokeSecret = ({ key }: AgentSecret) =>
    openConfirmation({
      title: 'Revoke API Key',
      body: 'Are you sure you want to remove this API key?',
      danger: true,
      primaryButtonText: 'Remove',
      onSubmit: () => updateVariable({ key, value: null }),
    });

  return { revokeSecret };
}
