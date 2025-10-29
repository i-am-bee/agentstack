/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';
import { useFormContext } from 'react-hook-form';

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import { useListTools } from '#modules/tools/api/queries/useListTools.ts';

import type { RunRunFormValues } from '../types';
import classes from './ChatTools.module.scss';
import { ChatSupportedTools } from './constants';
import { ToolToggle } from './ToolToggle';

export function ChatTools() {
  const { setValue, watch } = useFormContext<RunRunFormValues>();
  const { data, isPending, error, isRefetching, refetch } = useListTools();
  const tools = data?.tools.filter(({ name }) => ChatSupportedTools.includes(name));
  const chatTools = watch('tools');

  const handleToggle = useCallback(
    ({ tool, checked }: { tool: string; checked: boolean }) => {
      if (checked) {
        setValue('tools', chatTools ? [...chatTools, tool] : [tool]);
      } else {
        setValue('tools', chatTools ? chatTools.filter((item) => item !== tool) : []);
      }
    },
    [chatTools, setValue],
  );

  if (error && !tools) {
    return (
      <ErrorMessage
        title="Failed to load tools."
        onRetry={refetch}
        isRefetching={isRefetching}
        subtitle={error?.message}
      />
    );
  }

  return (
    <div className={classes.root}>
      <h2 className={classes.heading}>Tools</h2>

      <ul className={classes.list}>
        {!isPending ? (
          tools?.map((tool) => (
            <li key={tool.name}>
              <ToolToggle
                tool={tool}
                toggled={Boolean(chatTools?.includes(tool.name))}
                onToggle={(checked) => handleToggle({ tool: tool.name, checked })}
              />
            </li>
          ))
        ) : (
          <SkeletonItems
            count={3}
            render={(idx) => (
              <li key={idx}>
                <ToolToggle.Skeleton />
              </li>
            )}
          />
        )}
      </ul>
    </div>
  );
}
