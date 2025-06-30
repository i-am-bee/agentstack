/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, InlineLoading, ModalBody, ModalFooter, ModalHeader, TextInput } from '@carbon/react';
import { useCallback } from 'react';
import { useForm } from 'react-hook-form';

import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';
import type { MissingEnvs } from '#modules/providers/api/types.ts';

import { useUpdateVariable } from '../api/mutations/useUpdateVariable';
import classes from './AddRequiredVariablesModal.module.scss';

interface Props extends ModalProps {
  missingEnvs: NonNullable<MissingEnvs>;
}

export function AddRequiredVariablesModal({ missingEnvs, onRequestClose, ...modalProps }: Props) {
  const {
    register,
    handleSubmit,
    formState: { isValid },
  } = useForm<FormValues>({
    mode: 'onChange',
  });

  const { mutate: updateVariable, isPending } = useUpdateVariable({
    onSuccess: onRequestClose,
  });

  const onSubmit = useCallback(
    (body: FormValues) => {
      updateVariable({ body });
    },
    [updateVariable],
  );

  return (
    <Modal {...modalProps}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Required environment variables</h2>

        <p className={classes.description}>
          This agent requires the use of environment variables for one or more tools. Your API key grants access to your
          data and services—if exposed, it can lead to unauthorized access, data leaks, or unexpected charges.
        </p>
      </ModalHeader>

      <ModalBody>
        <form>
          <div className={classes.stack}>
            {missingEnvs.map((env) => (
              <TextInput
                id={env.name}
                key={env.name}
                labelText={env.name}
                helperText={env.description}
                {...register(env.name, { required: env.required })}
              />
            ))}
          </div>
        </form>
      </ModalBody>

      <ModalFooter>
        <Button kind="ghost" onClick={() => onRequestClose()}>
          Cancel
        </Button>

        <Button onClick={() => handleSubmit(onSubmit)()} disabled={isPending || !isValid}>
          {isPending ? <InlineLoading description="Saving&hellip;" /> : 'Save'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

type FormValues = {
  [key: string]: string;
};
