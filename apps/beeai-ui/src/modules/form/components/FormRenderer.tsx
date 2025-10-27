/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormRender } from 'beeai-sdk';
import { FormProvider, useForm } from 'react-hook-form';

import { AgentRunHeader } from '#modules/agents/components/detail/AgentRunHeader.tsx';
import { AgentWelcomeMessage } from '#modules/agents/components/detail/AgentWelcomeMessage.tsx';
import { isNotNull } from '#utils/helpers.ts';

import type { RunFormValues } from '../types';
import { getDefaultValues } from '../utils';
import { FormActionBar } from './FormActionBar';
import { FormFields } from './FormFields';
import classes from './FormRenderer.module.scss';

interface Props {
  definition: FormRender;
  defaultHeading?: string | null;
  showHeading?: boolean;
  isDisabled?: boolean;
  showRunSettings?: boolean;
  onSubmit: (values: RunFormValues) => void;
}

export function FormRenderer({
  definition,
  defaultHeading,
  showHeading: showHeadingProp = true,
  showRunSettings,
  isDisabled,
  onSubmit,
}: Props) {
  const { id, title: heading = defaultHeading, description, columns, submit_label, fields } = definition;

  const defaultValues = getDefaultValues(fields);

  const form = useForm<RunFormValues>({ defaultValues });

  const showHeading = showHeadingProp && isNotNull(heading);
  const showHeader = showHeading || Boolean(description);

  return (
    <FormProvider {...form}>
      <form id={id} onSubmit={form.handleSubmit(onSubmit)}>
        <fieldset disabled={isDisabled} className={classes.root}>
          {showHeader && (
            <AgentRunHeader heading={showHeading ? heading : undefined}>
              {description && <AgentWelcomeMessage>{description}</AgentWelcomeMessage>}
            </AgentRunHeader>
          )}

          <FormFields fields={fields} columns={columns} />

          <FormActionBar
            submitLabel={submit_label ?? 'Submit'}
            showRunSettings={showRunSettings}
            showSubmitButton={!isDisabled}
          />
        </fieldset>
      </form>
    </FormProvider>
  );
}
