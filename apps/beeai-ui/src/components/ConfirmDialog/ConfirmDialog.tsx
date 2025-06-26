/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import { TrashCan } from '@carbon/react/icons';
import clsx from 'clsx';
import type { ComponentType, ReactNode } from 'react';

import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { Modal } from '../Modal/Modal';
import classes from './ConfirmDialog.module.scss';

export interface ConfirmDialogProps {
  title: ReactNode;
  body?: ReactNode;
  primaryButtonText?: string;
  secondaryButtonText?: string;
  danger?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  icon?: ComponentType;
  onSubmit: () => void;
}

export function ConfirmDialog({
  title,
  body,
  primaryButtonText,
  secondaryButtonText,
  danger,
  icon: Icon,
  onSubmit,
  onRequestClose,
  size = 'sm',
  ...props
}: ConfirmDialogProps & ModalProps) {
  const onSubmitClick = () => {
    onRequestClose();
    onSubmit();
  };
  return (
    <Modal size={size} {...props} className={clsx(classes.root)}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h3 className={classes.heading}>{title}</h3>
      </ModalHeader>

      <ModalBody>{body}</ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          {secondaryButtonText ?? 'Cancel'}
        </Button>

        <Button
          onClick={onSubmitClick}
          kind={danger ? 'danger' : 'secondary'}
          data-modal-primary-focus
          renderIcon={Icon}
        >
          <span>{primaryButtonText ?? 'Ok'}</span>
          {danger && <TrashCan />}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
