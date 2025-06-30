/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Search } from '@carbon/icons-react';
import type { TextInputProps } from '@carbon/react';
import { TextInput } from '@carbon/react';
import type { ReactNode } from 'react';
import { useId } from 'react';

import classes from './TableViewToolbar.module.scss';

interface Props {
  searchProps: Partial<Omit<TextInputProps, 'id' | 'size' | 'hideLabel'>>;
  button: ReactNode;
}

export function TableViewToolbar({ searchProps, button }: Props) {
  const id = useId();

  return (
    <div className={classes.root}>
      <div className={classes.search}>
        <Search />

        <TextInput labelText="Search" {...searchProps} id={`${id}:search`} size="lg" hideLabel />
      </div>

      <div className={classes.button}>{button}</div>
    </div>
  );
}
