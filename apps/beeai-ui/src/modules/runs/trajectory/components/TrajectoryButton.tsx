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

import { ChevronDown } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import classes from './TrajectoryButton.module.scss';

interface Props {
  isOpen?: boolean;
  onClick?: MouseEventHandler;
}

export function TrajectoryButton({ isOpen, onClick }: Props) {
  return (
    <Button
      kind="ghost"
      size="sm"
      renderIcon={ChevronDown}
      className={clsx(classes.root, { [classes.isOpen]: isOpen })}
      onClick={onClick}
    >
      How did I get this answer?
    </Button>
  );
}
