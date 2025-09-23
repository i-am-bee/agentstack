/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ModalBody, ModalHeader } from '@carbon/react';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import { EditSecretForm } from './EditSecretForm';
import classes from './SecretsAddModal.module.scss';

interface Props extends ModalProps {
  secret: AgentSecret;
  updateSecret: (key: string, value: string) => void;
}

export function SecretsAddModal({ secret, updateSecret, ...modalProps }: Props) {
  const { name, description } = secret;

  return (
    <Modal {...modalProps} className={classes.root}>
      <ModalHeader>
        <h2>
          <span>{name}</span>
        </h2>

        <p className={classes.description}>{description}</p>
      </ModalHeader>

      <ModalBody>
        <EditSecretForm secret={secret} updateSecret={updateSecret} onSuccess={modalProps.onRequestClose} />
      </ModalBody>
    </Modal>
  );
}
