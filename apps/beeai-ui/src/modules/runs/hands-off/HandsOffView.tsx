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
