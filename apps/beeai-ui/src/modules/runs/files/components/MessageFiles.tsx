/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ChatMessage } from '#modules/runs/chat/types.ts';

import { FileCard } from './FileCard';
import { FileCardsList } from './FileCardsList';

interface Props {
  message: ChatMessage;
  className?: string;
}

export function MessageFiles({ message, className }: Props) {
  const files = message.files ?? [];
  const hasFiles = files.length > 0;

  return hasFiles ? (
    <FileCardsList className={className}>
      {files.map(({ key, filename, href }) => (
        <li key={key}>
          <FileCard href={href} filename={filename} />
        </li>
      ))}
    </FileCardsList>
  ) : null;
}
