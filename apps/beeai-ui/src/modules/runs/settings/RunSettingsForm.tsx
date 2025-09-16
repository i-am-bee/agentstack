/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { match } from 'ts-pattern';

import type { AgentSettings, SettingsRender } from '#api/a2a/extensions/ui/settings.ts';

import { useAgentRun } from '../contexts/agent-run';
import classes from './RunSettingsForm.module.scss';
import { SingleSelectSettingsField } from './SingleSelectSettingsField';
import { ToggleSettingsField } from './ToggleSettingsField';

interface Props {
  settingsRender: SettingsRender;
}

export function RunSettingsForm({ settingsRender }: Props) {
  const { onUpdateSettings, getSettings } = useAgentRun();

  const form = useForm<AgentSettings>({
    defaultValues: getSettings(),
  });

  const values = form.watch();

  useEffect(() => {
    onUpdateSettings(values);
  }, [onUpdateSettings, values]);

  return (
    <FormProvider {...form}>
      <form className={classes.root}>
        {settingsRender.fields.map((group) => {
          return match(group)
            .with({ type: 'checkbox_group' }, ({ id, fields }) => (
              <div key={id}>
                {fields.map((field) => (
                  <ToggleSettingsField
                    key={`${id}.${field.id}`}
                    field={{ id: `${id}.values.${field.id}`, label: field.label }}
                  />
                ))}
              </div>
            ))
            .with({ type: 'single_select' }, ({ id, options }) => (
              <SingleSelectSettingsField
                key={id}
                field={{
                  id,
                  options,
                }}
              />
            ))
            .exhaustive();
        })}
      </form>
    </FormProvider>
  );
}
