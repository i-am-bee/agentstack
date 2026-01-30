/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  CheckboxGroupField,
  CheckboxGroupFieldValue,
  SettingsCheckboxGroupFieldValue,
  SettingsDemands,
  SettingsFormRender,
  SettingsFormValues,
  SettingsSingleSelectFieldValue,
  SettingsValues,
  SingleSelectField,
  SingleSelectFieldValue,
} from 'agentstack-sdk';
import mapValues from 'lodash/mapValues';
import { match } from 'ts-pattern';

export function getInitialSettingsFormValues(settingsForm: SettingsFormRender | null) {
  const fields = settingsForm?.fields ?? [];

  const defaults = fields.reduce<SettingsFormValues>((valuesAcc, field) => {
    valuesAcc[field.id] = match(field)
      .with({ type: 'checkbox_group' }, ({ fields }) => {
        const values = fields.reduce<NonNullable<CheckboxGroupFieldValue['value']>>((acc, field) => {
          acc[field.id] = field.default_value;

          return acc;
        }, {});

        return {
          type: 'checkbox_group',
          value: values,
        } satisfies CheckboxGroupFieldValue;
      })
      .with({ type: 'singleselect' }, ({ default_value }) => {
        return {
          type: 'singleselect',
          value: default_value,
        } satisfies SingleSelectFieldValue;
      })
      .exhaustive();

    return valuesAcc;
  }, {});

  return defaults;
}

export function transformLegacySettingsDemandsToSettingsForm(
  settingsDemands: SettingsDemands | null,
): SettingsFormRender | null {
  if (!settingsDemands) {
    return null;
  }

  const settingsForm = {
    fields: settingsDemands.fields.map((field) =>
      match(field)
        .with(
          { type: 'checkbox_group' },
          ({ id, fields }) =>
            ({
              id,
              label: '',
              type: 'checkbox_group',
              fields: fields.map(({ id, label, default_value }) => ({
                id,
                label,
                type: 'checkbox',
                content: label,
                default_value,
              })),
            }) satisfies CheckboxGroupField,
        )
        .with(
          { type: 'single_select' },
          ({ id, label, options, default_value }) =>
            ({
              id,
              label,
              type: 'singleselect',
              options: options.map(({ value, label }) => ({
                id: value,
                label,
              })),
              default_value,
            }) satisfies SingleSelectField,
        )
        .exhaustive(),
    ),
  };

  return settingsForm;
}

export function transformSettingsFormValuesToLegacySettingsValues(settingsValues: SettingsFormValues): SettingsValues {
  const legacySettingsValues = mapValues(settingsValues, (value) =>
    match(value)
      .with(
        { type: 'checkbox_group' },
        ({ value: groupValue }) =>
          ({
            type: 'checkbox_group',
            values: mapValues(groupValue ?? {}, (value) => ({ value: value ?? false })),
          }) satisfies SettingsCheckboxGroupFieldValue,
      )
      .with(
        { type: 'singleselect' },
        ({ value }) =>
          ({
            type: 'single_select',
            value: value ?? '',
          }) satisfies SettingsSingleSelectFieldValue,
      )
      .exhaustive(),
  );

  return legacySettingsValues;
}
