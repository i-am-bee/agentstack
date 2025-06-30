/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { SplitPanesView } from '#components/SplitPanesView/SplitPanesView.tsx';

import { useHandsOff } from '../contexts/hands-off';
import { FileUploadDropzone } from '../files/components/FileUploadDropzone';
import { useFileUpload } from '../files/contexts';
import { HandsOffText } from './HandsOffText';
import classes from './HandsOffView.module.scss';

export function HandsOffView({ children }: PropsWithChildren) {
  const { output } = useHandsOff();
  const { dropzone } = useFileUpload();

  const className = classes.mainContent;

  return (
    <SplitPanesView
      mainContent={
        <div {...(dropzone ? dropzone.getRootProps({ className }) : { className })}>
          <Container size="sm">{children}</Container>

          {dropzone?.isDragActive && <FileUploadDropzone />}
        </div>
      }
      leftPane={children}
      rightPane={<HandsOffText />}
      isSplit={Boolean(output)}
      spacing="md"
    />
  );
}
