/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ModalBody, ModalHeader } from '@carbon/react';
import clsx from 'clsx';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import { EditSecretForm } from './EditSecretForm';
import classes from './SecretsAddModal.module.scss';

interface Props extends ModalProps {
  secret: AgentSecret;
  className?: string;
}

export function SecretsAddModal({ secret, className, ...modalProps }: Props) {
  const { name, description } = secret;

  return (
    <Modal
      {...modalProps}
      className={clsx(classes.root, className)}
      size="sm"
      selectorPrimaryFocus="[data-modal-initial-focus]"
    >
      <ModalHeader>
        <h2>
          <span>{name}</span>
        </h2>

        <p className={classes.description}>{description}</p>
      </ModalHeader>

      <ModalBody>
        <EditSecretForm secret={secret} onSuccess={modalProps.onRequestClose} />
      </ModalBody>
    </Modal>
  );
}
