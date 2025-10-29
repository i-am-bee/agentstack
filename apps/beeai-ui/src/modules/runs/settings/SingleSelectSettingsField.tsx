/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SettingsSingleSelectFieldValue } from 'agentstack-sdk';
import { useController } from 'react-hook-form';

import { RadioSelect } from '#components/RadioSelect/RadioSelect.tsx';

export function SingleSelectSettingsField({
  field,
}: {
  field: { id: string; label: string; options: { value: string; label: string }[] };
}) {
  const { id, label } = field;

  const {
    field: { onChange, value },
  } = useController<{ [key: string]: SettingsSingleSelectFieldValue }, `${typeof id}.value`>({
    name: `${id}.value`,
  });

  return (
    <RadioSelect
      name="radio-button-vertical-group"
      label={label}
      value={value}
      options={field.options}
      onChange={onChange}
    />
  );
}
