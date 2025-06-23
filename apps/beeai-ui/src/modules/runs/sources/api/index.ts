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

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

// TODO:
export async function readSourceMetadata({ url }: { url: string }) {
  const response = await api.POST('/api/v1/ui/source', { params: { query: { url } } });

  return ensureData(response);

  // const title: string | undefined = 'beeai-platform: Discover, run, and compose AI';

  // return {
  //   title: title ?? url,
  //   description:
  //     'Orchestrate agents into workflows — regardless of how or where they were built . Key features. Feature, Description. ACP Native, Built from the ground.',
  //   faviconUrl: 'https://github.githubassets.com/favicons/favicon.svg',
  // };
}
