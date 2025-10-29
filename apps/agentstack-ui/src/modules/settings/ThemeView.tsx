/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { RadioButton, RadioButtonGroup } from '@carbon/react';
import { useId } from 'react';

import { useTheme } from '#contexts/Theme/index.ts';
import { ThemePreference } from '#contexts/Theme/theme-context.ts';

export function ThemeView() {
  const { themePreference, setThemePreference } = useTheme();
  const id = useId();

  return (
    <RadioButtonGroup
      legendText="Theme"
      valueSelected={themePreference}
      onChange={(value) => {
        setThemePreference(value as ThemePreference);
      }}
      orientation="vertical"
      name="theme"
    >
      <RadioButton labelText="Sync with system" value={ThemePreference.System} id={`${id}:system`} />
      <RadioButton labelText="Light" value={ThemePreference.Light} id={`${id}:light`} />
      <RadioButton labelText="Dark" value={ThemePreference.Dark} id={`${id}:dark`} />
    </RadioButtonGroup>
  );
}
