import { NextRequest } from 'next/server';

async function handler(req: NextRequest, { params }: { params: { path: string[] } }) {
  const url = new URL(process.env.API_URL!);
  const search = req.nextUrl.search;
  const { path } = await params;

  const targetUrl = `${url}api/${path.join('/')}${search}`;

  console.log(targetUrl);

  const { method, headers, body } = req;

  const res = await fetch(targetUrl, {
    method,
    headers,
    body,
    // @ts-expect-error - TS does not know `duplex`, but it's required by some
    // browsers for stream requests https://fetch.spec.whatwg.org/#ref-for-dom-requestinit-duplex
    duplex: body ? 'half' : undefined,
  });

  // forward headers and stream
  return new Response(res.body, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'text/plain',
    },
  });
}

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
