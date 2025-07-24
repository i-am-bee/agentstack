/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Send, StopFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';

import { useFileUpload } from '#modules/files/contexts/index.ts';

import { useAgentRun } from '../contexts/agent-run';

interface Props {
  disabled?: boolean;
}

export function RunSubmit({ disabled }: Props) {
  const { isPending, cancel } = useAgentRun();
  const { isPending: isFileUploadPending } = useFileUpload();

  if (isPending) {
    return (
      <Button
        renderIcon={StopFilled}
        kind="ghost"
        size="sm"
        hasIconOnly
        iconDescription="Cancel"
        onClick={(event) => {
          cancel();

          event.preventDefault();
        }}
      />
    );
  }

  return (
    <Button
      type="submit"
      renderIcon={Send}
      kind="ghost"
      size="sm"
      hasIconOnly
      iconDescription={isFileUploadPending ? 'Files are uploading' : 'Send'}
      disabled={disabled}
    />
  );
}
