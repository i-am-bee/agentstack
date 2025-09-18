/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useEffect, useState } from 'react';

import { Modal } from '#components/Modal/Modal.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import type { AgentRequestSecrets } from '../contexts/agent-settings/types';
import { ApiKeysAddModal } from './ApiKeysAddModal';
import classes from './ApiKeysModal.module.scss';
import { ToolCardsList } from './ToolCardsList';

interface ApiKeyModalProps extends ModalProps {
  requestedSecrets: AgentRequestSecrets;
  updateApiKey: (key: string, value: string) => void;
  revokeApiKey: (key: string) => void;
}

export function ApiKeysModal({ onRequestClose, ...modalProps }: ApiKeyModalProps) {
  const [step, setStep] = useState(Step.Landing);

  const { openModal } = useModal();

  const isLanding = step === Step.Landing;

  const closeAddModal = useCallback(() => {
    setStep(Step.Landing);

    console.log('close');
  }, []);

  const openAddModal = useCallback(() => {
    setStep(Step.Add);

    openModal(({ onRequestClose, ...props }) => (
      <ApiKeysAddModal
        {...props}
        onRequestClose={(force) => {
          closeAddModal();

          onRequestClose(force);
        }}
      />
    ));
  }, [openModal, closeAddModal]);

  useEffect(() => {
    openAddModal();

    return () => {
      closeAddModal();
    };
  }, [openAddModal, closeAddModal]);

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
        <ToolCardsList />
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
