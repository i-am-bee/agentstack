/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { match } from 'ts-pattern';

import type { SettingsResponseValue } from '#api/a2a/extensions/ui/settings.ts';
import { settingsExtension, type SettingsRender } from '#api/a2a/extensions/ui/settings.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';

import { useAgentRun } from './contexts/agent-run';

const settingsExtensionExtractor = extractServiceExtensionDemands(settingsExtension);

function SettingsRender({ settingsRender }: { settingsRender: SettingsRender }) {
  const { changeSettings } = useAgentRun();

  const initialValues = useMemo(() => {
    return settingsRender.fields.reduce((acc, field) => {
      acc[field.id] = {
        type: field.type,
        value: field.default_value,
      };
      return acc;
    }, {});
  }, [settingsRender]);

  const form = useForm<Record<string, SettingsResponseValue>>({
    defaultValues: initialValues,
  });

  useEffect(() => {
    changeSettings(initialValues);
  }, [changeSettings, initialValues]);

  return (
    <FormProvider {...form}>
      <form>
        {settingsRender.fields.map((field) => {
          return match(field)
            .with({ type: 'checkbox' }, ({ id, label, default_value }) => {
              return (
                <label key={id}>
                  {label}{' '}
                  <input
                    type="checkbox"
                    {...form.register(`${id}.value`, {
                      onChange: () => {
                        changeSettings(form.getValues());
                      },
                    })}
                    key={id}
                    defaultChecked={default_value}
                  />
                </label>
              );
            })
            .otherwise(() => {
              throw new Error('Unsupported field type');
            });
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
