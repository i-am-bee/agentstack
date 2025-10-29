/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessage } from '#modules/messages/types.ts';
import { getMessageFiles } from '#modules/messages/utils.ts';

import { FileCard } from './FileCard';
import { FileCardsList } from './FileCardsList';

interface Props {
  message: UIMessage;
  className?: string;
}

export function MessageFiles({ message, className }: Props) {
  const files = getMessageFiles(message);
  const hasFiles = files.length > 0;

  if (!hasFiles) {
    return null;
  }

  return (
    <FileCardsList className={className}>
      {files.map(({ id, filename, url }) => (
        <li key={id}>
          <FileCard href={url} filename={filename} />
        </li>
      ))}
    </FileCardsList>
  );
}
