/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface FeedbackForm {
  categories?: FeedbackCategory[];
  comment?: string;
  vote?: FeedbackVote;
}

export type FeedbackCategory = {
  id: string;
  label: string;
};

export enum FeedbackVote {
  Up = 'up',
  Down = 'down',
}
