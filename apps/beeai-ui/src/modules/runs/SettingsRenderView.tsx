/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkbox, Select, SelectItem } from '@carbon/react';
import { useCallback, useEffect, useMemo } from 'react';
import { FormProvider, useForm, useFormContext } from 'react-hook-form';
import { match } from 'ts-pattern';

import type { AgentSettings, CheckboxFieldValue, SingleSelectFieldValue } from '#api/a2a/extensions/ui/settings.ts';
import { settingsExtension, type SettingsRender } from '#api/a2a/extensions/ui/settings.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';

import { useAgentRun } from './contexts/agent-run';

const settingsExtensionExtractor = extractServiceExtensionDemands(settingsExtension);

function CheckboxSettingsField({ field, onChanged }: { field: { label: string; id: string }; onChanged: () => void }) {
  const { id, label } = field;
  const { register } = useFormContext<{ [key: string]: CheckboxFieldValue }>();

  return <Checkbox id={id} labelText={label} {...register(`${id}.value`, { onChange: onChanged })} />;
}

function SingleSelectSettingsField({
  field,
  onChanged,
}: {
  field: { id: string; options: { value: string; label: string }[] };
  onChanged: () => void;
}) {
  const { id } = field;

  const { register } = useFormContext<{ [key: string]: SingleSelectFieldValue }>();

  return (
    <Select
      id={id}
      {...register(`${id}.value`, {
        onChange: onChanged,
      })}
    >
      {field.options.map(({ value, label }) => (
        <SelectItem key={value} value={value} text={label} />
      ))}
    </Select>
  );
}

function SettingsRender({ settingsRender }: { settingsRender: SettingsRender }) {
  const { changeSettings } = useAgentRun();

  const initialValues = useMemo(() => {
    return settingsRender.fields.reduce<AgentSettings>((valuesAcc, field) => {
      valuesAcc[field.id] = match(field)
        .with({ type: 'checkbox_group' }, ({ fields }) => {
          const values = fields.reduce<Record<string, CheckboxFieldValue>>((acc, field) => {
            acc[field.id] = {
              value: field.default_value,
            };

            return acc;
          }, {});

          return { type: 'checkbox_group', values } as const;
        })
        .with({ type: 'single_select' }, ({ default_value }) => {
          return { type: 'single_select', value: default_value } as const;
        })
        .exhaustive();

      return valuesAcc;
    }, {});
  }, [settingsRender]);

  const form = useForm<AgentSettings>({
    defaultValues: initialValues,
  });

  const changeCurrentSettings = useCallback(() => {
    changeSettings(form.getValues());
  }, [changeSettings, form]);

  useEffect(() => {
    changeSettings(initialValues);
  }, [changeSettings, initialValues]);

  return (
    <FormProvider {...form}>
      <form>
        {settingsRender.fields.map((group) => {
          return match(group)
            .with({ type: 'checkbox_group' }, ({ id, fields }) => {
              return fields.map((field) => {
                return (
                  <CheckboxSettingsField
                    key={`${id}.${field.id}`}
                    field={{ id: `${id}.values.${field.id}`, label: field.label }}
                    onChanged={changeCurrentSettings}
                  />
                );
              });
            })
            .with({ type: 'single_select' }, ({ id, options }) => {
              return (
                <SingleSelectSettingsField
                  key={id}
                  field={{
                    id,
                    options,
                  }}
                  onChanged={changeCurrentSettings}
                />
              );
            })
            .exhaustive();
        })}
      </form>
    </FormProvider>
  );
}

export function SettingsRenderView() {
  const { agent } = useAgentRun();

  const settingsRender = useMemo(() => {
    const { extensions } = agent.capabilities;
    const settingsRender = extensions && settingsExtensionExtractor(extensions);

    return settingsRender ?? undefined;
  }, [agent.capabilities]);

  if (!settingsRender) {
    return <></>;
  }

  return <SettingsRender settingsRender={settingsRender} />;
}
