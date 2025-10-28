/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSettings, SettingsDemands } from 'beeai-sdk';
import { useEffect } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { match } from 'ts-pattern';

import { useAgentDemands } from '../contexts/agent-demands';
import classes from './RunSettingsForm.module.scss';
import { SingleSelectSettingsField } from './SingleSelectSettingsField';
import { ToggleSettingsField } from './ToggleSettingsField';

interface Props {
  settingsDemands: SettingsDemands;
}

export function RunSettingsForm({ settingsDemands }: Props) {
  const { selectedSettings, onUpdateSettings } = useAgentDemands();

  const form = useForm<AgentSettings>({
    defaultValues: selectedSettings,
  });

  useEffect(() => {
    const subscription = form.watch((values: AgentSettings) => {
      onUpdateSettings(values);
    });

    return () => subscription.unsubscribe();
  }, [form, onUpdateSettings]);

  return (
    <FormProvider {...form}>
      <form className={classes.root}>
        {settingsDemands.fields.map((group) => {
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
            .with({ type: 'single_select' }, ({ id, label, options }) => (
              <SingleSelectSettingsField
                key={id}
                field={{
                  id,
                  label,
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
