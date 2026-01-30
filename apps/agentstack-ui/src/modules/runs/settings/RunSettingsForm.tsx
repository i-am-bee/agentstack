/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SettingsFormRender, SettingsFormValues } from 'agentstack-sdk';
import { useEffect } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { match } from 'ts-pattern';

import { useAgentDemands } from '../contexts/agent-demands';
import classes from './RunSettingsForm.module.scss';
import { SingleSelectSettingsField } from './SingleSelectSettingsField';
import { ToggleSettingsField } from './ToggleSettingsField';

interface Props {
  settingsForm: SettingsFormRender;
}

export function RunSettingsForm({ settingsForm }: Props) {
  const { selectedSettings, onUpdateSettings } = useAgentDemands();

  const form = useForm<SettingsFormValues>({
    defaultValues: selectedSettings,
  });

  useEffect(() => {
    const subscription = form.watch((values: SettingsFormValues) => {
      onUpdateSettings(values);
    });

    return () => subscription.unsubscribe();
  }, [form, onUpdateSettings]);

  return (
    <FormProvider {...form}>
      <form className={classes.root}>
        {settingsForm.fields.map((group) =>
          match(group)
            .with({ type: 'checkbox_group' }, (groupField) => (
              <div key={groupField.id}>
                {groupField.fields.map((field) => (
                  <ToggleSettingsField key={field.id} field={field} groupField={groupField} />
                ))}
              </div>
            ))
            .with({ type: 'singleselect' }, (field) => <SingleSelectSettingsField key={field.id} field={field} />)
            .exhaustive(),
        )}
      </form>
    </FormProvider>
  );
}
