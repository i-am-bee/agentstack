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

import { Container } from '#components/layouts/Container.tsx';
import { SplitPanesView } from '#components/SplitPanesView/SplitPanesView.tsx';

import { useCompose } from '../contexts';
import { SequentialSetup } from '../sequential/SequentialSetup';
import { ComposeResult } from './ComposeResult';

export function ComposeView() {
  const { result } = useCompose();

  const sequentialSetup = <SequentialSetup />;

  return (
    <SplitPanesView
      mainContent={<Container size="sm">{sequentialSetup}</Container>}
      leftPane={sequentialSetup}
      rightPane={<ComposeResult />}
      isSplit={Boolean(result)}
    />
  );
}
