/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, InlineLoading, ModalBody, ModalFooter, ModalHeader } from '@carbon/react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import type { SubmitHandler } from 'react-hook-form';
import { FormProvider, useForm } from 'react-hook-form';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { useCreateConnector } from '../api/mutations/useCreateConnector';
import { type AddConnectorForm, addConnectorFormSchema } from '../types';
import { AddConnectorFormFields } from './AddConnectorFormFields';
import classes from './AddConnectorModal.module.scss';
import { ConnectorPresetsList } from './ConnectorPresetsList';

export function AddConnectorModal({ onRequestClose, ...modalProps }: ModalProps) {
  const [view, setView] = useState<View>(View.Browse);

  const { mutate: createConnector, isPending } = useCreateConnector({ onSuccess: () => onRequestClose() });

  const form = useForm({
    mode: 'onChange',
    resolver: zodResolver(addConnectorFormSchema),
  });

  const onSubmit: SubmitHandler<AddConnectorForm> = ({ url, clientId, clientSecret, name }) => {
    createConnector({
      url,
      match_preset: false,
      client_id: clientId,
      client_secret: clientSecret,
      metadata: { name },
    });
  };

  const toggleView = () => setView((view) => (view === View.Add ? View.Browse : View.Add));

  const {
    handleSubmit,
    formState: { isValid },
  } = form;

  const isAddView = view === View.Add;

  return (
    <Modal {...modalProps}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Add connector</h2>
      </ModalHeader>

      <ModalBody>
        <div className={classes.body}>
          <Button kind="tertiary" size="sm" onClick={toggleView} className={classes.toggleBtn}>
            {isAddView ? 'Browse connectors' : 'Add custom connector'}
          </Button>

          {isAddView ? (
            <FormProvider {...form}>
              <form onSubmit={handleSubmit(onSubmit)}>
                <AddConnectorFormFields />
              </form>
            </FormProvider>
          ) : (
            <ConnectorPresetsList />
          )}
        </div>
      </ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          Cancel
        </Button>

        {isAddView && (
          <Button onClick={handleSubmit(onSubmit)} disabled={isPending || !isValid}>
            {isPending ? <InlineLoading description="Adding&hellip;" /> : 'Add connector'}
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
}

enum View {
  Add = 'add',
  Browse = 'browse',
}
