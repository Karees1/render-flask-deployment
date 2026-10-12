# Next.js (App Router)

A Route Handler gives you the redirect with no extra server. Works on Vercel and self-hosted.

`app/q/[slug]/route.ts`
```ts
import { NextRequest, NextResponse } from "next/server";
import { getLink, logScan } from "@/lib/qr";   // your DB layer (Prisma, Drizzle, Supabase, ...)

export const dynamic = "force-dynamic";          // never cache the redirect

export async function GET(req: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;                 // params is a Promise in Next 15+
  const link = await getLink(slug);
  if (!link) return new NextResponse("Not found", { status: 404 });

  const headers = { "Cache-Control": "no-store" };
  if (!link.active) {
    return NextResponse.redirect(link.fallback ?? new URL("/", req.url), { status: 302, headers });
  }

  logScan(slug, req.headers.get("user-agent") ?? "").catch(() => {}); // fire and forget

  const dest = new URL(link.destination);
  dest.searchParams.set("utm_source", dest.searchParams.get("utm_source") ?? "qr");
  dest.searchParams.set("utm_medium", dest.searchParams.get("utm_medium") ?? "print");
  if (link.label) dest.searchParams.set("utm_campaign", dest.searchParams.get("utm_campaign") ?? link.label);

  return NextResponse.redirect(dest, { status: 302, headers });
}
```

Notes:
- **Do not** use `next.config.js` `redirects()` for this: it is baked in at build time, so changing a destination needs a redeploy and a `permanent: true` flag emits a cached 301.
- On Vercel, a serverless function is fine for scan volume; if you want edge speed, add `export const runtime = "edge"` and use an edge-compatible DB client (Supabase REST, Vercel KV, Upstash).
- On Vercel, fire-and-forget promises can be cut off when the response returns. Wrap the logging in `after()` from `next/server` (Next 15+) or `waitUntil` so the scan is still recorded.
- Generate the PDF with the Python script at build/ops time, or call it from an API route if clients self-serve.
