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

import { useMCPClient } from '#contexts/MCPClient/index.ts';
import { useQuery } from '@tanstack/react-query';
import { toolKeys } from '../keys';
import { ListToolsParams } from '../types';

interface Props {
  params?: ListToolsParams;
}

export function useListTools({ params }: Props = {}) {
  const client = useMCPClient();

  const query = useQuery({
    queryKey: toolKeys.list(params),
    queryFn: () => client!.listTools(params),
    enabled: Boolean(client),
  });

  return query;
}
