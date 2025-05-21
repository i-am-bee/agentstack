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

import { useMemo } from 'react';

import { MainNav } from '#components/MainNav/MainNav.tsx';
import { TracesTooltip } from '#components/MainNav/TracesTooltip.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { useIsNavSectionActive } from '#hooks/useIsNavSectionActive.ts';
import { usePhoenix } from '#modules/phoenix/api/queries/usePhoenix.ts';
import { routes, sections } from '#utils/router.ts';
import { APP_NAME, PHOENIX_SERVER_TARGET } from '#utils/vite-constants.ts';

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
      linkComponent={TransitionLink}
      items={items.map(({ section, ...item }) => ({ ...item, isActive: section && isSectionActive(section) }))}
    />
  );
}
