/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { experimental_streamedQuery as streamedQuery, useQuery } from '@tanstack/react-query';
import { EventSourceParserStream } from 'eventsource-parser/stream';

import { readProviderBuildLogs } from '..';
import { providerBuildKeys } from '../keys';
import { readableToAsyncIterable } from '../utils';

interface Props {
  id: string | undefined;
}

export function useProviderBuildLogs({ id = '' }: Props) {
  const query = useQuery({
    queryKey: providerBuildKeys.log({ id }),
    queryFn: streamedQuery({
      streamFn: async () => {
        const data = await readProviderBuildLogs({ id });

        const stream = data?.pipeThrough(new TextDecoderStream()).pipeThrough(new EventSourceParserStream());

        return readableToAsyncIterable(stream);
      },
    }),
    enabled: Boolean(id),
  });

  return query;
}
