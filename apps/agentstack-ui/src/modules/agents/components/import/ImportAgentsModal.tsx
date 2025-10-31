/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Button,
  InlineLoading,
  InlineNotification,
  ModalBody,
  ModalFooter,
  ModalHeader,
  RadioButton,
  RadioButtonGroup,
  Select,
  SelectItem,
  TextInput,
} from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useEffect, useId } from 'react';
import { useController, useForm } from 'react-hook-form';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { Modal } from '#components/Modal/Modal.tsx';
import type { ModalProps } from '#contexts/Modal/modal-context.ts';
import { useImportAgent } from '#modules/agents/hooks/useImportAgent.ts';
import type { ImportAgentFormValues } from '#modules/agents/types.ts';
import { ProviderSource } from '#modules/providers/types.ts';

import classes from './ImportAgentsModal.module.scss';

export function ImportAgentsModal({ onRequestClose, ...modalProps }: ModalProps) {
  const id = useId();

  const { agent, logs, actionRequired, providersToUpdate, isPending, error, importAgent } = useImportAgent();

  const {
    register,
    handleSubmit,
    resetField,
    formState: { isValid },
    control,
  } = useForm<ImportAgentFormValues>({
    mode: 'onChange',
    defaultValues: {
      source: ProviderSource.GitHub,
    },
  });

  const { field: sourceField } = useController<ImportAgentFormValues, 'source'>({ name: 'source', control });
  const { field: actionField } = useController<ImportAgentFormValues, 'action'>({ name: 'action', control });

  const showLogs = isPending && logs.length > 0;

  const onSubmit = useCallback(
    async (values: ImportAgentFormValues) => {
      await importAgent(values);

      resetField('action');
      resetField('providerId');
    },
    [importAgent, resetField],
  );

  useEffect(() => {
    resetField('location');
  }, [sourceField.value, resetField]);

  return (
    <Modal {...modalProps}>
      <ModalHeader buttonOnClick={() => onRequestClose()}>
        <h2>Add new agent</h2>
      </ModalHeader>

      <ModalBody>
        <form onSubmit={handleSubmit(onSubmit)} className={clsx(classes.form, { [classes.showLogs]: showLogs })}>
          {agent ? (
            <p>
              <strong>{agent.name}</strong> agent added successfully.
            </p>
          ) : isPending ? (
            <>
              <InlineLoading className={classes.loading} description="Adding an agent&hellip;" />

              {showLogs && (
                <CodeSnippet className={classes.logs} forceExpand withBorder autoScroll>
                  {logs.join('\n')}
                </CodeSnippet>
              )}
            </>
          ) : actionRequired ? (
            <div className={classes.stack}>
              <h3 className={classes.subheading}>Existing agents detected. What would you like to do?</h3>

              <RadioButtonGroup
                name={actionField.name}
                legendText="Action"
                valueSelected={actionField.value}
                onChange={actionField.onChange}
                disabled={isPending}
                orientation="vertical"
              >
                <RadioButton labelText="Add new agent" value="add_provider" />
                <RadioButton labelText="Update existing agent" value="update_provider" />
              </RadioButtonGroup>

              {actionField.value === 'update_provider' && providersToUpdate && (
                <Select
                  id={`${id}:provider`}
                  size="lg"
                  labelText="Select agent to update"
                  {...register('providerId', { required: true, disabled: isPending })}
                >
                  {providersToUpdate.map(({ id, source }) => (
                    <SelectItem key={id} text={source} value={id} />
                  ))}
                </Select>
              )}
            </div>
          ) : (
            <div className={classes.stack}>
              <RadioButtonGroup
                name={sourceField.name}
                legendText="Select the source of your agent provider"
                valueSelected={sourceField.value}
                onChange={sourceField.onChange}
                disabled={isPending}
              >
                <RadioButton labelText="GitHub" value={ProviderSource.GitHub} />
                <RadioButton labelText="Container image" value={ProviderSource.Docker} />
              </RadioButtonGroup>

              {sourceField.value === ProviderSource.GitHub ? (
                <TextInput
                  id={`${id}:location`}
                  size="lg"
                  labelText="GitHub repository URL"
                  placeholder="Enter your agent’s GitHub repository URL"
                  {...register('location', { required: true, disabled: isPending })}
                />
              ) : (
                <TextInput
                  id={`${id}:location`}
                  size="lg"
                  labelText="Container image URL"
                  placeholder="Enter your agent’s container image URL"
                  {...register('location', { required: true, disabled: isPending })}
                />
              )}
            </div>
          )}

          {error && !isPending && (
            <InlineNotification kind="error" title={error.title} subtitle={error.message} lowContrast />
          )}
        </form>
      </ModalBody>

      {!agent && (
        <ModalFooter>
          <Button
            type="submit"
            onClick={handleSubmit(onSubmit)}
            disabled={isPending || !isValid || (actionRequired && !actionField.value)}
          >
            {isPending ? <InlineLoading description="Adding&hellip;" /> : 'Add new agent'}
          </Button>
        </ModalFooter>
      )}
    </Modal>
  );
}
