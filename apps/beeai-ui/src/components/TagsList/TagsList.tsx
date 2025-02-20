/**
 * Copyright 2025 IBM Corp.
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

import { TagSkeleton } from '@carbon/react';
import clsx from 'clsx';
import { ReactElement } from 'react';
import classes from './TagsList.module.scss';

interface Props {
  tags: ReactElement[];
  className?: string;
}

export function TagsList({ tags, className }: Props) {
  return (
    <ul className={clsx(classes.root, className)}>
      {tags.map((tag, idx) => (
        <li key={idx}>{tag}</li>
      ))}
    </ul>
  );
}

interface SkeletonProps {
  length?: number;
  className?: string;
}

TagsList.Skeleton = function TagsListSkeleton({ length = 1, className }: SkeletonProps) {
  return (
    <div className={clsx(classes.root, className)}>
      {Array.from({ length }).map((_, idx) => (
        <TagSkeleton key={idx} />
      ))}
    </div>
  );
};
