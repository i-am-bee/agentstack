import { z } from 'zod';

export interface A2AExtension<T extends string, D extends any> {
  getSchema: () => z.ZodSchema<Partial<Record<T, D>>>;
  getKey: () => T;
}
