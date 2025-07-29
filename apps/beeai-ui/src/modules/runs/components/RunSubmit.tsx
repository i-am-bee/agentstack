/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Send, StopFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';

interface Props {
  isPending: boolean;
  isFileUploadPending: boolean;
  disabled: boolean;
  onCancel: () => void;
}

export function RunSubmit({ isPending, isFileUploadPending, disabled, onCancel }: Props) {
  if (isPending) {
    return (
      <Button
        renderIcon={StopFilled}
        kind="ghost"
        size="sm"
        hasIconOnly
        iconDescription="Cancel"
        onClick={(event) => {
          onCancel();

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
