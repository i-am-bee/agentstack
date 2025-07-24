import { A2AExtension } from './a2aExtension';

export const getExtensionData =
  <T extends string, D extends any>(extension: A2AExtension<T, D>) =>
  (metadata: Record<string, unknown> | undefined) => {
    const parsed = extension.getSchema().parse(metadata || {});
    if (parsed[extension.getKey()]) {
      return parsed[extension.getKey()];
    }

    return undefined;
  };
