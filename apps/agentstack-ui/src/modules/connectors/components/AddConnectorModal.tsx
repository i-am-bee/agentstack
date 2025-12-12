/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, InlineLoading, ModalBody, ModalFooter, ModalHeader, TextInput } from '@carbon/react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useId } from 'react';
import type { SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';

import { useCreateConnector } from '../api/mutations/useCreateConnector';
import { type AddConnectorForm, addConnectorFormSchema } from '../types';
import classes from './AddConnectorModal.module.scss';

export function AddConnectorModal({ onRequestClose, ...modalProps }: ModalProps) {
  const id = useId();

  const { mutate: createConnector, isPending } = useCreateConnector({ onSuccess: onRequestClose });

  const {
    register,
    handleSubmit,
    formState: { isValid, errors },
  } = useForm({
    mode: 'onChange',
    resolver: zodResolver(addConnectorFormSchema),
  });

  const onSubmit: SubmitHandler<AddConnectorForm> = useCallback(
    ({ url, clientId, clientSecret, name }) => {
      createConnector({
        url,
        match_preset: false,
        client_id: clientId,
        client_secret: clientSecret,
        metadata: { name },
      });
    },
    [createConnector],
  );

  return (
    <Modal {...modalProps}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Add connector</h2>
      </ModalHeader>

      <ModalBody>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className={classes.stack}>
            <TextInput
              id={`${id}:name`}
              labelText="Name"
              invalid={Boolean(errors.name)}
              invalidText={errors.name?.message}
              {...register('name')}
            />

            <TextInput
              id={`${id}:url`}
              labelText="URL"
              invalid={Boolean(errors.url)}
              invalidText={errors.url?.message}
              {...register('url')}
            />

            <TextInput
              id={`${id}:client-id`}
              labelText="Client ID"
              invalid={Boolean(errors.clientId)}
              invalidText={errors.clientId?.message}
              {...register('clientId', { deps: ['clientSecret'] })}
            />

            <TextInput
              id={`${id}:client-secret`}
              labelText="Client secret"
              invalid={Boolean(errors.clientSecret)}
              invalidText={errors.clientSecret?.message}
              {...register('clientSecret')}
            />
          </div>
        </form>
      </ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          Cancel
        </Button>

        <Button onClick={handleSubmit(onSubmit)} disabled={isPending || !isValid}>
          {isPending ? <InlineLoading description="Adding&hellip;" /> : 'Add connector'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
