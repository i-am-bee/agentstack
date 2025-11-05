/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { useAgentSecrets } from '../contexts/agent-secrets';
import classes from './SecretsModal.module.scss';

export function SecretsModal({ onRequestClose, ...modalProps }: ModalProps) {
  const { demandedSecrets } = useAgentSecrets();

  return (
    <Modal {...modalProps} size="lg" rootClassName={classes.root} preventCloseOnClickOutside>
      <ModalHeader>
        <p className={classes.descrition}>
          This agent uses the following API keys. You can configure it now to get a full capability use or later at
          runtime
        </p>
      </ModalHeader>

      <ModalBody>
        <ul className={classes.root}>
          {demandedSecrets.map((secret) => (
            <li key={secret.key}>
              ...
              {/* <SecretCard secret={secret} /> */}
            </li>
          ))}
        </ul>
      </ModalBody>

      <ModalFooter>
        <Button disabled={demandedSecrets.some(({ isReady }) => !isReady)} onClick={() => onRequestClose()}>
          Save changes
        </Button>
      </ModalFooter>
    </Modal>
  );
}
