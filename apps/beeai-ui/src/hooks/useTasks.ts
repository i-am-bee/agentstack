/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

const tasks = new Map<string, NodeJS.Timeout>();

export function useTasks() {
  const addTask = ({ id, type, task, delay }: { id: string; type: TaskType; task: () => void; delay: number }) => {
    const taskId = getTaskId({ id, type });

    if (tasks.has(taskId)) return;

    const intervalId = setInterval(task, delay);

    tasks.set(taskId, intervalId);
  };

  const removeTask = ({ id, type }: { id: string; type: TaskType }) => {
    const taskId = getTaskId({ id, type });

    if (!tasks.has(taskId)) return;

    const intervalId = tasks.get(taskId);

    clearInterval(intervalId);

    tasks.delete(taskId);
  };

  return {
    tasks,
    addTask,
    removeTask,
  };
}

export enum TaskType {
  ProviderStatusCheck = 'ProviderStatusCheck',
}

function getTaskId({ id, type }: { id: string; type: TaskType }) {
  return `${type}_${id}`;
}
