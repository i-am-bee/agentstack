/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FeedbackCategory } from './types';

export const FEEDBACK_FORM_DEFAULTS = {
  categories: [],
  comment: '',
};

export const FEEDBACK_CATEGORIES: FeedbackCategory[] = [
  {
    id: 'accuracy',
    label: 'Accuracy',
  },
  {
    id: 'comprehensiveness',
    label: 'Comprehensiveness',
  },
  {
    id: 'information_retrieval',
    label: 'Information retrieval',
  },
  {
    id: 'sophistication',
    label: 'Sophistication',
  },
  {
    id: 'latency',
    label: 'Latency',
  },
  {
    id: 'other_content',
    label: 'Other',
  },
];

export const FEEDBACK_DIALOG_OFFSET = {
  mainAxis: 24,
};
