/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Meta, StoryObj } from '@storybook/react';

import { createKcPageStory } from '../KcPageStory';

const { KcPageStory } = createKcPageStory({ pageId: 'delete-credential.ftl' });

const meta = {
  title: 'login/delete-credential.ftl',
  component: KcPageStory,
} satisfies Meta<typeof KcPageStory>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <KcPageStory />,
};
export const WithCustomCredentialLabel: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        credentialLabel: 'Test Credential',
        url: { loginAction: '/login-action' },
      }}
    />
  ),
};
