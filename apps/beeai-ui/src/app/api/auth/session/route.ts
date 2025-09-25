/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { handlers, auth } from '#app/(auth)/auth.ts';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);

  try {
    const session = await auth();

    if (!session) {
      return NextResponse.json(null);
    }

    const { access_token, ...filteredSession } = session;

    return NextResponse.json(filteredSession);
  } catch (error) {
    console.error('Error while fetching session:', error);
    return NextResponse.json(null, { status: 500 });
  }
}

export const { POST } = handlers;
