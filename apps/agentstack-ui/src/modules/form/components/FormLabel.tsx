/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import type { LabelHTMLAttributes } from 'react';

export function FormLabel({ className, children, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label {...props} className={clsx('cds--label', className)}>
      {children}
    </label>
  );
}
