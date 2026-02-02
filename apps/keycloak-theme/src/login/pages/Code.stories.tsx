/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Meta, StoryObj } from "@storybook/react";

import { createKcPageStory } from "../KcPageStory";

const { KcPageStory } = createKcPageStory({ pageId: "code.ftl" });

const meta = {
  title: "login/code.ftl",
  component: KcPageStory,
} satisfies Meta<typeof KcPageStory>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <KcPageStory />,
};
export const WithErrorCode: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        code: {
          success: false,
          error: "Failed to generate code",
        },
      }}
    />
  ),
};
export const WithFrenchLanguage: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        locale: {
          currentLanguageTag: "fr",
        },
        code: {
          success: true,
          code: "XYZ789",
        },
      }}
    />
  ),
};
export const WithHtmlErrorMessage: Story = {
  render: () => (
    <KcPageStory
      kcContext={{
        code: {
          success: false,
          error:
            "Something went wrong. <a href='https://example.com'>Try again</a>",
        },
      }}
    />
  ),
};
