/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { LabelHTMLAttributes } from 'react';

export function FormLabel({ children, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label {...props} className="cds--label">
      {children}
    </label>
  );
}
