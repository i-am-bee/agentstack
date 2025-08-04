/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { UISourcePart } from '#modules/messages/types.ts';
import { useSources } from '#modules/sources/contexts/index.ts';
import { isSourceActive } from '#modules/sources/utils.ts';

import { InlineCitationButton } from './InlineCitationButton';
import classes from './InlineCitations.module.scss';

interface Props {
  sources: UISourcePart[] | undefined;
}

export function InlineCitations({ sources = [], children }: PropsWithChildren<Props>) {
  const { activeSidePanel, openSidePanel } = useApp();
  const { activeSource, setActiveSource } = useSources();
  const hasSources = sources.length > 0;

  if (!hasSources) {
    return children;
  }

  return (
    <span className={classes.root}>
      <span className={classes.content}>{children}</span>

      <span className={classes.list}>
        {sources.map((source) => {
          const { id, messageId, number } = source;
          const isActive = activeSidePanel === SidePanelVariant.Sources && isSourceActive(source, activeSource);

          return (
            <sup key={id} className={clsx(classes.item, { [classes.isActive]: isActive })}>
              <InlineCitationButton
                source={source}
                isActive={isActive}
                onClick={() => {
                  setActiveSource({ number, messageId });
                  openSidePanel(SidePanelVariant.Sources);
                }}
              />
            </sup>
          );
        })}
      </span>
    </span>
  );
}
