/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Toggle } from '@carbon/react';
import { useController } from 'react-hook-form';

import type { CheckboxFieldValue } from '#api/a2a/extensions/ui/settings.ts';

import classes from './ToggleSettingsField.module.scss';

export function ToggleSettingsField({ field }: { field: { label: string; id: string } }) {
  const { id, label } = field;

  const {
    field: { onChange, value },
  } = useController<{ [key: string]: CheckboxFieldValue }>({
    name: `${id}.value`,
  });

  return (
    <Toggle
      className={classes.root}
      id={id}
      labelA={label}
      labelB={label}
      size="sm"
      onToggle={onChange}
      toggled={Boolean(value)}
    />
  );
}
