/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface SourceReference {
  key: string;
  number: number;
  url: string;
  startIndex: number;
  endIndex: number;
  messageKey: string;
  title?: string;
  description?: string;
}

export interface SourceMetadata {
  title: string;
  description?: string;
  faviconUrl?: string;
}

export interface ResolvedSource extends SourceReference {
  metadata: SourceMetadata;
}

export interface SourcesData {
  [messageKey: string]: SourceReference[];
}
