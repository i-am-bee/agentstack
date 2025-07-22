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

import { InlineCitationButton } from './InlineCitationButton';
import classes from './InlineCitations.module.scss';

interface Props {
  sources: UISourcePart[] | undefined;
}

export function InlineCitations({ sources = [], children }: PropsWithChildren<Props>) {
  const { activeSidePanel, openSidePanel } = useApp();
  const { activeSource, setActiveSource } = useSources();

  return sources.length > 0 ? (
    <span className={classes.root}>
      <span className={classes.content}>{children}</span>

      <span className={classes.list}>
        {sources.map((source) => {
          const { id, messageId } = source;
          const isActive = activeSidePanel === SidePanelVariant.Sources && activeSource?.id === id;

          return (
            <sup key={id} className={clsx(classes.item, { [classes.isActive]: isActive })}>
              <InlineCitationButton
                source={source}
                isActive={isActive}
                onClick={() => {
                  setActiveSource({ id, messageId });
                  openSidePanel(SidePanelVariant.Sources);
                }}
              />
            </sup>
          );
        })}
      </span>
    </span>
  ) : (
    children
  );
}
