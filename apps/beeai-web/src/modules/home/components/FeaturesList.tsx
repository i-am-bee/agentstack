/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { ComponentType, PropsWithChildren } from 'react';

import classes from './FeaturesList.module.scss';
import { TwoColumnGrid } from './TwoColumnGrid';

export interface FeatureItem {
  icon: ComponentType;
  title: string;
  content: string;
}

interface Props {
  items: FeatureItem[];
  className?: string;
}

export function FeaturesList({ className, items }: PropsWithChildren<Props>) {
  return (
    <TwoColumnGrid className={clsx(classes.root, className)} as="ul">
      {items.map(({ icon: Icon, title, content }, idx) => (
        <li key={idx}>
          <Icon />
          <div className={classes.content}>
            <strong>{title}</strong>
            <span>{content}</span>
          </div>
        </li>
      ))}
    </TwoColumnGrid>
  );
}
