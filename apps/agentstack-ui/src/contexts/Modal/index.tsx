/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useContext } from 'react';

import type { ConfirmDialogProps } from '#components/ConfirmDialog/ConfirmDialog.tsx';
import { ConfirmDialog } from '#components/ConfirmDialog/ConfirmDialog.tsx';

import { ModalContext } from './modal-context';

export function useModal() {
  const openModal = useContext(ModalContext);

  const openConfirmation = useCallback(
    (confirmProps: ConfirmDialogProps) => {
      openModal((props) => <ConfirmDialog {...confirmProps} {...props} />);
    },
    [openModal],
  );

  return { openModal, openConfirmation };
}
