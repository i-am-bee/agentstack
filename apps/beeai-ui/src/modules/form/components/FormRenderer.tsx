/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import type { FormRender } from 'beeai-sdk';
import { FormProvider, useForm } from 'react-hook-form';

import { AgentHeader } from '#modules/agents/components/AgentHeader.tsx';
import { AgentName } from '#modules/agents/components/AgentName.tsx';
import { AgentWelcomeMessage } from '#modules/agents/components/AgentWelcomeMessage.tsx';

import type { RunFormValues } from '../types';
import { getDefaultValues } from '../utils';
import { FormFields } from './FormFields';
import classes from './FormRenderer.module.scss';

interface Props {
  definition: FormRender;
  defaultHeading?: string | null;
  showHeading?: boolean;
  isDisabled?: boolean;
  onSubmit: (values: RunFormValues) => void;
}

export function FormRenderer({ definition, defaultHeading, showHeading = true, isDisabled, onSubmit }: Props) {
  const { id, title, description, columns, submit_label, fields } = definition;

  const defaultValues = getDefaultValues(fields);

  const form = useForm<RunFormValues>({ defaultValues });

  const heading = title ?? defaultHeading;
  const hasHeading = Boolean(showHeading && heading);
  const showHeader = hasHeading || description;

  return (
    <FormProvider {...form}>
      <form id={id} onSubmit={form.handleSubmit(onSubmit)}>
        <fieldset disabled={isDisabled} className={classes.root}>
          {showHeader && (
            <AgentHeader>
              {hasHeading && <AgentName>{heading}</AgentName>}

              {description && <AgentWelcomeMessage>{description}</AgentWelcomeMessage>}
            </AgentHeader>
          )}

          <FormFields fields={fields} columns={columns} />

          {!isDisabled && (
            <>
              <div className={classes.buttons}>
                <Button type="submit" size="md">
                  {submit_label ?? 'Submit'}
                </Button>
              </div>
            </>
          )}
        </fieldset>
      </form>
    </FormProvider>
  );
}
