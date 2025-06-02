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

'use client';

import { Filter } from '@carbon/icons-react';
import { Button, Checkbox, CheckboxGroup, Link, Popover, PopoverContent } from '@carbon/react';
import { useState } from 'react';

import classes from './FiltersPopover.module.scss';

interface Option {
  label: string;
  count: number;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export interface Group {
  label: string;
  options: Option[];
}

interface FiltersPopoverProps {
  groups: Group[];
  onClearAll: () => void;
  toggleButtonClassName?: string;
}

export function FiltersPopover({ groups, onClearAll, toggleButtonClassName }: FiltersPopoverProps) {
  const [open, setOpen] = useState(false);
  const toggleOpen = () => setOpen(!open);
  const areFiltersActive = groups.some((group) => group.options.some((option) => option.checked));

  return (
    <Popover open={open} isTabTip onRequestClose={() => setOpen(false)} align="bottom-right">
      <div className={classes.toggleButtonContainer}>
        <Button
          className={toggleButtonClassName}
          kind={areFiltersActive ? 'primary' : 'ghost'}
          size="md"
          renderIcon={Filter}
          hasIconOnly
          onClick={toggleOpen}
          iconDescription="Filters"
        />
      </div>

      <PopoverContent>
        <div className={classes.container}>
          <Link
            href="#clear-all-filters"
            onClick={(event) => {
              event.preventDefault();
              onClearAll();
              toggleOpen();
            }}
            className={classes.clear}
          >
            Clear all
          </Link>

          {groups.map((group) => (
            <CheckboxGroup key={group.label} legendText={group.label}>
              {group.options.map(({ label, count, checked, onChange }) => (
                <Checkbox
                  key={label}
                  id={label}
                  labelText={`${label} (${count})`}
                  checked={checked}
                  onChange={(_, { checked }) => onChange(checked)}
                />
              ))}
            </CheckboxGroup>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
