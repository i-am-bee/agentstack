/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { match } from 'ts-pattern';

import type { AgentSettings, CheckboxFieldValue, SettingsRender } from '#api/a2a/extensions/ui/settings.ts';

export function getSettingsRenderDefaultValues(settingsRender: SettingsRender) {
  const defaults = settingsRender?.fields.reduce<AgentSettings>((valuesAcc, field) => {
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

  return defaults;
}
