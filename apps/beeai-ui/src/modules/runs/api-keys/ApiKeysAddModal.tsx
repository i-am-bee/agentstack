/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Tools } from '@carbon/icons-react';
import { ModalBody, ModalHeader } from '@carbon/react';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { AddApiKeyForm, AddApiKeyFormVariant } from './AddApiKeyForm';
import classes from './ApiKeysAddModal.module.scss';

export function ApiKeysAddModal({ ...modalProps }: ModalProps) {
  const toolName = 'Slack';

  return (
    <Modal {...modalProps} className={classes.root}>
      <ModalHeader>
        <h2>
          <Tools size={32} />

          <span>{toolName}</span>
        </h2>

        <p className={classes.description}>
          Provide your {toolName} API key to allow this agent access to your channels and personal messages.
        </p>
      </ModalHeader>

      <ModalBody>
        <AddApiKeyForm toolName={toolName} variant={AddApiKeyFormVariant.Modal} />
      </ModalBody>
    </Modal>
  );
}
