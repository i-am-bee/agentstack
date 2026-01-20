/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ApiErrorException, isApiError, isHttpError } from 'agentstack-sdk';

import type { QueryMetadataError } from '#contexts/QueryProvider/types.ts';
import type { Toast } from '#contexts/Toast/toast-context.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { NEXTAUTH_URL, TRUST_PROXY_HEADERS } from '#utils/constants.ts';
import { isNotNull } from '#utils/helpers.ts';
import { createMarkdownCodeBlock, createMarkdownSection, joinMarkdownSections } from '#utils/markdown.ts';

import { A2AExtensionError, TaskCanceledError } from './errors';

export function getErrorTitle(error: unknown) {
  if (error instanceof A2AExtensionError) {
    return 'errors' in error.error ? 'Multiple errors occurred' : error.error.title;
  }

  if (error instanceof TaskCanceledError) {
    return 'Task canceled';
  }

  return typeof error === 'object' && isNotNull(error) && 'title' in error ? (error.title as string) : undefined;
}

export function getErrorMessage(error: unknown, includeMessage = true) {
  if (!includeMessage) {
    return;
  }

  if (isApiError(error)) {
    return createApiErrorMessage(error);
  } else if (error instanceof A2AExtensionError) {
    return createA2AErrorMessage(error);
  }

  return typeof error === 'object' && isNotNull(error) && 'message' in error ? (error.message as string) : undefined;
}

export function logErrorDetails(error: unknown) {
  console.error(error);

  if (error instanceof ApiErrorException && 'details' in error.apiError) {
    console.error(error.apiError.details);
  }
}

export async function fetchEntity<T>(fetchFn: () => Promise<T>): Promise<T | undefined> {
  try {
    return await fetchFn();
  } catch (error) {
    logErrorDetails(error);

    return undefined;
  }
}

export async function getProxyHeaders(headers: Headers, url?: URL) {
  const forwardedHost = (TRUST_PROXY_HEADERS && headers.get('x-forwarded-host')) || url?.host || NEXTAUTH_URL?.host;
  const forwardedProto =
    (TRUST_PROXY_HEADERS && headers.get('x-forwarded-proto')) ||
    (url?.protocol ?? NEXTAUTH_URL?.protocol)?.replace(/:$/, '');
  const forwardedFor = TRUST_PROXY_HEADERS && (headers.get('x-forwarded-for') || headers.get('x-real-ip'));

  let forwardedFromXForwarded = `host=${forwardedHost};proto=${forwardedProto}`;
  if (forwardedFor) {
    forwardedFromXForwarded = `${forwardedFromXForwarded};for=${forwardedFor}`;
  }

  const forwarded = [
    ...(TRUST_PROXY_HEADERS && headers.get('forwarded') ? [headers.get('forwarded')] : []),
    forwardedFromXForwarded,
  ].join(',');

  return { forwardedHost, forwardedProto, forwardedFor, forwarded };
}

export function buildErrorToast({ metadata = {}, error }: { metadata?: QueryMetadataError; error: unknown }): Toast {
  const { title = 'An error occurred', includeErrorMessage } = metadata;

  return {
    kind: 'error',
    title: getErrorTitle(error) ?? title,
    message: joinMarkdownSections([metadata.message, getErrorMessage(error, includeErrorMessage)]),
    renderMarkdown: true,
  };
}

function createApiErrorMessage(error: ApiErrorException) {
  const { message } = error.apiError;

  if (isHttpError(error)) {
    const { status, bodyText } = error.apiError.response;
    const heading = `${message} (${status})`;
    const parsedBody = typeof bodyText === 'string' ? maybeParseJson(bodyText) : null;

    if (parsedBody) {
      const { type, value } = parsedBody;

      return createMarkdownSection({
        heading,
        content:
          type === 'string'
            ? value
            : createMarkdownCodeBlock({
                snippet: value,
                language: 'json',
              }),
      });
    }

    return heading;
  }

  return message;
}

function createA2AErrorMessage(error: A2AExtensionError) {
  const {
    error: { message: errorMessage },
    context,
    stackTrace,
  } = error;

  const errors = 'errors' in error.error ? error.error.errors : [];
  const errorMessages = joinMarkdownSections(
    errors.map(({ title, message }) => createMarkdownSection({ heading: title, content: message })),
  );

  const contextMessage = context
    ? createMarkdownSection({
        heading: 'Context',
        content: createMarkdownCodeBlock({
          snippet: JSON.stringify(context, null, 2),
          language: 'json',
        }),
      })
    : undefined;
  const stackTraceMessage = stackTrace
    ? createMarkdownSection({
        heading: 'Stack Trace',
        content: createMarkdownCodeBlock({
          snippet: stackTrace,
        }),
      })
    : undefined;

  const message = joinMarkdownSections([errorMessage, errorMessages, contextMessage, stackTraceMessage]);

  return message;
}
