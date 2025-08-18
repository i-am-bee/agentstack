/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { ComponentType, PropsWithChildren, ReactNode } from 'react';

import classes from './FeaturesList.module.scss';
import { TwoColumnGrid } from './TwoColumnGrid';

interface FeatureItem {
  icon: ComponentType;
  content: ReactNode;
}

interface Props {
  items: FeatureItem[];
  className?: string;
}

export function FeaturesList({ className, items }: PropsWithChildren<Props>) {
  return (
    <TwoColumnGrid className={clsx(classes.root, className)} as="ul">
      {items.map(({ icon: Icon, content }, idx) => (
        <li key={idx}>
          <Icon />
          <span>{content}</span>
        </li>
      ))}
    </TwoColumnGrid>
  );
}
