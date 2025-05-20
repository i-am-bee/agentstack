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

import clsx from 'clsx';
import { forwardRef, type PropsWithChildren } from 'react';

import classes from './SidePanel.module.scss';

interface Props {
  variant: 'left' | 'right';
  isOpen?: boolean;
  className?: string;
}

export const SidePanel = forwardRef<HTMLElement, PropsWithChildren<Props>>(function SidePanel(
  { variant, isOpen, className, children },
  ref,
) {
  return (
    <aside
      ref={ref}
      className={clsx(
        classes.root,
        [classes[variant]],
        {
          [classes.isOpen]: isOpen,
        },
        className,
      )}
    >
      <div className={classes.content}>{children}</div>
    </aside>
  );
});
