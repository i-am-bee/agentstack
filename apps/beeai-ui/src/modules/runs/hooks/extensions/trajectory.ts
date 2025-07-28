import { z } from 'zod';
import { A2AExtension } from './a2aExtension';

const extensionKey = 'https://a2a-extensions.beeai.dev/trajectory/v1';
const trajectoryMetadataSchemaV1 = z
  .object({
    message: z.string(),
    tool_name: z.string(),
    tool_input: z.record(z.string(), z.unknown()),
    tool_outpyut: z.record(z.string(), z.unknown()),
  })
  .partial();

export type TrajectoryMetadata = z.infer<typeof trajectoryMetadataSchemaV1>;

export const trajectoryExtensionV1: A2AExtension<typeof extensionKey, TrajectoryMetadata> = {
  getSchema: () =>
    z
      .object({
        [extensionKey]: trajectoryMetadataSchemaV1,
      })
      .partial(),
  getKey: () => extensionKey,
};
