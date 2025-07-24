/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import type { Agent } from '../api/types';
import type { AgentsFiltersParams } from '../providers/AgentsFiltersProvider';
import { sortAgentsByName } from '../utils';

interface Props {
  agents: Agent[];
  filters: AgentsFiltersParams;
}

export function useFilteredAgents({ agents, filters }: Props) {
  const filteredAgents = useMemo(() => {
    const { search, frameworks, programmingLanguages, licenses } = filters;

    const searchQuery = search.trim().toLowerCase();
    const searchRegex = searchQuery ? new RegExp(searchQuery, 'i') : null;

    return agents
      ?.filter((agent) => {
        const { name, description, ui } = agent;
        const { framework, programming_language, license } = ui;

        if (frameworks.length && !frameworks.includes(framework ?? '')) {
          return false;
        }

        if (programmingLanguages.length && !programmingLanguages.includes(programming_language ?? '')) {
          return false;
        }

        if (licenses.length && !licenses.includes(license ?? '')) {
          return false;
        }

        if (searchRegex) {
          const nameMatch = searchRegex.test(name);
          const descriptionMatch = description ? searchRegex.test(description) : false;

          if (!nameMatch && !descriptionMatch) {
            return false;
          }
        }

        return true;
      })
      .sort(sortAgentsByName);
  }, [agents, filters]);

  return { filteredAgents, filteredCount: filteredAgents.length };
}
