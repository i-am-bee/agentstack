/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useContext } from 'react';

import type { ConfirmDialogProps } from '#components/ConfirmDialog/ConfirmDialog.tsx';
import { ConfirmDialog } from '#components/ConfirmDialog/ConfirmDialog.tsx';

import { ModalContext } from './modal-context';

export function useModal() {
  const openModal = useContext(ModalContext);

  const openConfirmation = (confirmProps: ConfirmDialogProps) => {
    openModal((props) => <ConfirmDialog {...confirmProps} {...props} />);
  };

  return { openModal, openConfirmation };
}
