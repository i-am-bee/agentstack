/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSettings, SettingsCheckboxFieldValue, SettingsDemands } from 'beeai-sdk';
import { match } from 'ts-pattern';

export function getSettingsRenderDefaultValues(settingsRender: SettingsDemands) {
  const defaults = settingsRender?.fields.reduce<AgentSettings>((valuesAcc, field) => {
    valuesAcc[field.id] = match(field)
      .with({ type: 'checkbox_group' }, ({ fields }) => {
        const values = fields.reduce<Record<string, SettingsCheckboxFieldValue>>((acc, field) => {
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
