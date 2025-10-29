/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Tool } from '../api/types';

interface Props {
  name: Tool['name'];
}

export function ToolName({ name }: Props) {
  return NAMES_MAP[name as keyof typeof NAMES_MAP] ?? name;
}

const NAMES_MAP = {
  search: 'Search',
  wikipedia: 'Wikipedia',
  weather: 'Weather',
};
