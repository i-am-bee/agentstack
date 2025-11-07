import type { FormResponseValue } from './common/form';
import { requestFormExtension } from './ui/request-form';

export type RunFormValues = Record<string, FormResponseValue>;

export type InputRequiredResponses = Partial<{
  form: Record<string, FormResponseValue>;
}>;

export const handleInputRequired = () => {
  const resolveMetadata = async (responses: InputRequiredResponses) => {
    const metadata: Record<string, unknown> = {};

    if (responses.form) {
      metadata[requestFormExtension.getUri()] = {
        values: responses.form,
      };
    }

    return metadata;
  };

  return {
    resolveMetadata,
  };
};
