/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SignIn } from '#modules/auth/Signin.tsx';

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function SignInPage({ searchParams }: PageProps) {
  const callbackUrl = (await searchParams).callbackUrl;

  return <SignIn callbackUrl={typeof callbackUrl == 'string' ? callbackUrl : undefined} />;
}
