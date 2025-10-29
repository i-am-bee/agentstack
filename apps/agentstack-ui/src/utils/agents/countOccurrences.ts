/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Agent } from '#modules/agents/api/types.ts';
import { compareStrings } from '#utils/helpers.ts';

type AgentsCounts = Record<string, number>;
export type AgentsCountedOccurrence = { label: string; count: number }[];
type AgentsCountedOccurrences = {
  frameworks: AgentsCountedOccurrence;
  programming_languages: AgentsCountedOccurrence;
  licenses: AgentsCountedOccurrence;
};

export function countOccurrences(agents: Agent[]): AgentsCountedOccurrences {
  function updateCount(acc: AgentsCounts, value: string) {
    acc[value] = (acc[value] || 0) + 1;
  }

  const counts = agents.reduce(
    (acc, agent) => {
      const { framework, license, programming_language } = agent.ui;

      if (framework) {
        updateCount(acc.frameworks, framework);
      }

      if (license) {
        updateCount(acc.licenses, license);
      }

      if (programming_language) {
        updateCount(acc.programming_languages, programming_language);
      }

      return acc;
    },
    {
      frameworks: {} as AgentsCounts,
      programming_languages: {} as AgentsCounts,
      licenses: {} as AgentsCounts,
    },
  );

  return {
    frameworks: sort(counts.frameworks),
    programming_languages: sort(counts.programming_languages),
    licenses: sort(counts.licenses),
  };
}

// Sorts counts in descending order, with the option to prioritize (place first) a specific entry
function sort(counts: AgentsCounts, prioritize?: string): AgentsCountedOccurrence {
  return Object.entries(counts)
    .sort(([keyA, countA], [keyB, countB]) => {
      if (keyA === prioritize && keyB !== prioritize) {
        return -1; // A should come before B if A is the prioritized one
      }

      if (keyB === prioritize && keyA !== prioritize) {
        return 1; // B should come before A if B is the prioritized one
      }

      // If no prioritization is applied, and counts are not the same, sort by the count in descending order
      if (countA !== countB) {
        return countB - countA;
      }

      // If counts are the same, sort the keys alphabetically
      return compareStrings(keyA, keyB);
    })
    .map(([key, count]) => ({ label: key, count }));
}
