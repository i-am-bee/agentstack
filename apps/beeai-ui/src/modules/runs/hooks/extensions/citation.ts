import { z } from 'zod';
import { A2AExtension } from './a2aExtension';

const extensionKey = 'https://a2a-extensions.beeai.dev/citations/v1';
const citationMetadataSchemaV1 = z
  .object({
    url: z.string(),
    start_index: z.number(),
    end_index: z.number(),
    title: z.string(),
    description: z.string(),
  })
  .partial();

export type CitationMetadata = z.infer<typeof citationMetadataSchemaV1>;

export const citationExtensionV1: A2AExtension<typeof extensionKey, CitationMetadata> = {
  getSchema: () =>
    z
      .object({
        [extensionKey]: citationMetadataSchemaV1,
      })
      .partial(),
  getKey: () => extensionKey,
};
