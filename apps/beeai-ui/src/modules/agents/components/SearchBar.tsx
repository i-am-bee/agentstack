/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Search } from '@carbon/react';
import { useId } from 'react';

interface Props {
  search: string;
  onSearchChange: (search: string) => void;
}

export function SearchBar({ search, onSearchChange }: Props) {
  const id = useId();

  return (
    <div>
      <Search
        id={id}
        labelText="Search"
        placeholder="Search all models"
        size="lg"
        value={search}
        onChange={(event) => {
          onSearchChange(event.target.value);
        }}
      />
    </div>
  );
}
