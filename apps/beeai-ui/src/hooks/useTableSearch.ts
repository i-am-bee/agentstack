/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ChangeEvent } from 'react';
import { useCallback, useMemo, useState } from 'react';

interface Props<T> {
  entries: T[];
  fields: (keyof T)[];
}

export function useTableSearch<T>({ entries, fields }: Props<T>) {
  const [search, setSearch] = useState('');

  const onSearch = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
  }, []);

  const items = useMemo(() => {
    const searchQuery = search.trim().toLowerCase();

    if (!searchQuery) {
      return entries;
    }

    return entries.filter((item) => fields.some((field) => String(item[field]).toLowerCase().includes(searchQuery)));
  }, [search, entries, fields]);

  return {
    items,
    onSearch,
  };
}
