/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface FeedbackForm {
  vote?: FeedbackVote;
  categories?: FeedbackCategory[];
  comment?: string;
}

export type FeedbackCategory = {
  id: string;
  label: string;
};

export enum FeedbackVote {
  Up = 'up',
  Down = 'down',
}
