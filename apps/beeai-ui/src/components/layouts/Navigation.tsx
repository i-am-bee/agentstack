/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { MainNav } from '#components/MainNav/MainNav.tsx';
import { TracesTooltip } from '#components/MainNav/TracesTooltip.tsx';
import { useIsNavSectionActive } from '#hooks/useIsNavSectionActive.ts';
import { usePhoenix } from '#modules/phoenix/api/queries/usePhoenix.ts';
import { APP_NAME, PHOENIX_SERVER_TARGET } from '#utils/constants.ts';
import { routes, sections } from '#utils/router.ts';

export function Navigation() {
  const isSectionActive = useIsNavSectionActive();
  const { isPending, error, data: showPhoenixTab } = usePhoenix();

  const items = useMemo(
    () => [
      {
        label: <strong>{APP_NAME}</strong>,
        href: routes.home(),
      },
      {
        label: 'Agents',
        href: routes.agents(),
        section: sections.agents,
      },
      {
        label: 'Traces',
        href: `${PHOENIX_SERVER_TARGET}/projects`,
        isExternal: true,
        disabled:
          isPending || error || !showPhoenixTab || !PHOENIX_SERVER_TARGET
            ? {
                tooltip: <TracesTooltip />,
              }
            : undefined,
      },
    ],
    [error, isPending, showPhoenixTab],
  );

  return (
    <MainNav
      items={items.map(({ section, ...item }) => ({ ...item, isActive: section && isSectionActive(section) }))}
    />
  );
}
