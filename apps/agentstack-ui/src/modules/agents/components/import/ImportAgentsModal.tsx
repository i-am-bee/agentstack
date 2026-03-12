/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, InlineLoading, InlineNotification, ModalBody, ModalFooter, ModalHeader, TextInput } from '@carbon/react';
import clsx from 'clsx';
import { useId } from 'react';
import { useForm } from 'react-hook-form';

import { Modal } from '#components/Modal/Modal.tsx';
import { useApp } from '#contexts/App/index.ts';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';
import { useImportAgent } from '#modules/agents/hooks/useImportAgent.ts';
import type { ImportAgentFormValues } from '#modules/agents/types.ts';
import { ProviderSource } from '#modules/providers/types.ts';

import classes from './ImportAgentsModal.module.scss';

export function ImportAgentsModal({ onRequestClose, ...modalProps }: ModalProps) {
  const id = useId();

  const {
    config: { appName },
  } = useApp();

  const { agent, isPending, error, importAgent } = useImportAgent();

  const {
    register,
    handleSubmit,
    formState: { isValid, errors },
  } = useForm<ImportAgentFormValues>({
    mode: 'onTouched',
    defaultValues: {
      source: ProviderSource.Docker,
    },
  });

  const onSubmit = async (values: ImportAgentFormValues) => {
    await importAgent(values);
  };

  return (
    <Modal {...modalProps} className={classes.root}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Add new agent</h2>
      </ModalHeader>

      <ModalBody>
        <form onSubmit={handleSubmit(onSubmit)} className={classes.form}>
          {agent ? (
            <p>
              <strong>{agent.name}</strong> agent added successfully.
            </p>
          ) : isPending ? (
            <InlineLoading className={classes.loading} description="Adding an agent&hellip;" />
          ) : (
            <div className={classes.stack}>
              <p>Once your agent is published, it will be visible to everyone with access to {appName}.</p>

              <TextInput
                id={`${id}:location`}
                size="lg"
                hideLabel
                invalid={Boolean(errors.location)}
                invalidText={errors.location?.message}
                labelText="Container image URL"
                placeholder="Enter your agent's container image URL"
                {...register('location', {
                  required: "Enter your agent's location.",
                  disabled: isPending,
                  setValueAs: (value: string) => value.trim(),
                })}
              />
            </div>
          )}

          {error && !isPending && (
            <InlineNotification kind="error" title={error.title} subtitle={error.message} lowContrast />
          )}
        </form>
      </ModalBody>

      {!agent && (
        <ModalFooter>
          <Button type="submit" size="sm" onClick={handleSubmit(onSubmit)} disabled={isPending || !isValid}>
            {isPending ? <InlineLoading description="Adding&hellip;" /> : 'Add new agent'}
          </Button>
        </ModalFooter>
      )}
    </Modal>
  );
}
