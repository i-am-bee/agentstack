/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import { AuthError } from 'next-auth';

import { auth, getProvider, signIn } from '#app/(auth)/auth.ts';
import { routes } from '#utils/router.ts';

import { AuthErrorPage } from './AuthErrorPage';
import { AutoSignIn } from './AutoSignIn';

interface Props {
  callbackUrl?: string;
}

const authProvider = getProvider();

export async function SignInProviders({ callbackUrl: redirectTo = routes.home() }: Props) {
  if (!authProvider) {
    return null;
  }

  const session = await auth();
  const hasExistingToken = session?.user != null;

  if (hasExistingToken) {
    return <AuthErrorPage />;
  }

  return <AutoSignIn signIn={handleSignIn.bind(null, { providerId: authProvider.id, redirectTo })} />;
}

async function handleSignIn({ providerId, redirectTo }: { providerId: string; redirectTo: string }) {
  'use server';

  try {
    await signIn(providerId, { redirectTo });
  } catch (error) {
    // Sign-in can fail for a number of reasons, such as the user not existing, or the user not having the correct role.
    // In some cases, you may want to redirect to a custom error.
    if (error instanceof AuthError) {
      return redirect(routes.error({ error }));
    }

    throw error;
  }
}
