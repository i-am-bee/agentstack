/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Download } from '@carbon/icons-react';
import { Button } from '@carbon/react';

interface Props {
  filename: string;
  content: string;
}

export function DownloadButton({ filename, content }: Props) {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);

  return (
    <Button
      as="a"
      download={filename}
      href={url}
      target="_blank"
      kind="ghost"
      size="md"
      hasIconOnly
      iconDescription="Download"
      tooltipPosition="left"
    >
      <Download />
    </Button>
  );
}
