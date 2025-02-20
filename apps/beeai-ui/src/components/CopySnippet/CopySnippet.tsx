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

import { Checkmark, Copy } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { useState } from 'react';
import classes from './CopySnippet.module.scss';

interface Props {
  snippet: string;
  className?: string;
}

export function CopySnippet({ snippet, className }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopyClick = () => {
    navigator.clipboard.writeText(snippet);

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  return (
    <div className={clsx(classes.root, className)}>
      <code className={classes.content}>{snippet}</code>

      <div className={classes.button}>
        <IconButton label="Copy" kind="ghost" size="md" onClick={handleCopyClick} disabled={copied}>
          {copied ? <Checkmark /> : <Copy />}
        </IconButton>
      </div>
    </div>
  );
}
