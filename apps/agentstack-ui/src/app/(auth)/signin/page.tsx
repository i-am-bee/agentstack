/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SignInView } from '#modules/auth/components/SignInView.tsx';

interface Props {
  searchParams: Promise<{ callbackUrl?: string }>;
}

export default async function SignInPage({ searchParams }: Props) {
  const { callbackUrl } = await searchParams;

  return <SignInView callbackUrl={callbackUrl} />;
}
