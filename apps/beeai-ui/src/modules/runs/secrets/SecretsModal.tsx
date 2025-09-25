/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useState } from 'react';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { useAgentSecrets } from '../contexts/agent-secrets';
import { SecretCardsList } from './SecretCardsList';
import classes from './SecretsModal.module.scss';

export function SecretsModal({ onRequestClose, ...modalProps }: ModalProps) {
  const [step, setStep] = useState(Step.Landing);

  const { secrets, updateSecret } = useAgentSecrets();

  const isLanding = step === Step.Landing;

  const handleOpendAddModal = useCallback(() => {
    setStep(Step.Add);
  }, []);
  const handleCloseAddModal = useCallback(() => {
    setStep(Step.Landing);
  }, []);

  return (
    <Modal
      {...modalProps}
      size="lg"
      rootClassName={clsx(classes.root, { [classes.isHidden]: !isLanding })}
      preventCloseOnClickOutside
    >
      <ModalHeader>
        <p className={classes.description}>
          This agent uses the following API keys. You can configure it now to get a full capability use or later at
          runtime
        </p>
      </ModalHeader>

      <ModalBody>
        <SecretCardsList
          secrets={secrets}
          updateSecret={updateSecret}
          onCloseAddModal={handleCloseAddModal}
          onOpenAddModal={handleOpendAddModal}
        />
      </ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          Skip for now
        </Button>

        <Button disabled={secrets.some(({ isReady }) => !isReady)} onClick={() => onRequestClose()}>
          Continue
        </Button>
      </ModalFooter>
    </Modal>
  );
}

enum Step {
  Landing = 'landing',
  Add = 'add',
}
