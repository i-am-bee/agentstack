/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
