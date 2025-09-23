/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useState } from 'react';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import { SecretCardsList } from './SecretCardsList';
import classes from './SecretsModal.module.scss';

interface ApiKeyModalProps extends ModalProps {
  secrets: AgentSecret[];
  updateSecret: (key: string, value: string) => void;
  revokeSecret: (key: string) => void;
}

export function SecretsModal({ secrets, updateSecret, onRequestClose, ...modalProps }: ApiKeyModalProps) {
  const [step, setStep] = useState(Step.Landing);

  // const { openModal } = useModal();

  const isLanding = step === Step.Landing;

  // const closeAddModal = useCallback(() => {
  //   setStep(Step.Landing);

  //   console.log('close');
  // }, []);

  // useEffect(() => {
  //   openAddModal();

  //   return () => {
  //     closeAddModal();
  //   };
  // }, [openAddModal, closeAddModal]);

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
      className={clsx(classes.root, { [classes.isHidden]: !isLanding })}
      preventCloseOnClickOutside
    >
      <ModalHeader>
        <p className={classes.description}>
          This agent uses the following tools, would you like to add your API keys? This can also be done later during
          runtime if you choose to skip for now.
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

        <Button disabled>Continue</Button>
      </ModalFooter>
    </Modal>
  );
}

enum Step {
  Landing = 'landing',
  Add = 'add',
}
