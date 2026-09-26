// Old Cloudflare Pages host -> canonical domain.
// Exact-host match so branch-preview hosts (<hash>.mechanicdb-public.pages.dev)
// and the custom domain itself are never redirected. Everything else falls
// through to the static assets (404.html, _headers, _redirects unchanged).
const OLD_HOST = "mechanicdb-public.pages.dev";
const NEW_HOST = "mechanicdb.dataengineered.io";

// Pages whose files were deleted but whose old copies an edge cache kept serving
// after the deploy (/j1939/deutz, withdrawn 2026-09-26; the copies expire by
// 2026-10-03). Answered here, before the asset layer, with the locale's 404 page.
const REMOVED = /^\/(?:(es|de|fr|pt-br)\/)?j1939\/deutz\/?$/;

export async function onRequest({ request, env, next }) {
  const url = new URL(request.url);
  if (url.hostname === OLD_HOST) {
    url.hostname = NEW_HOST;
    return Response.redirect(url.toString(), 301);
  }
  const removed = url.pathname.match(REMOVED);
  if (removed) {
    const notFound = await env.ASSETS.fetch(new URL(removed[1] ? `/${removed[1]}/404` : "/404", url));
    const headers = new Headers(notFound.headers);
    headers.set("Cache-Control", "no-store");
    return new Response(notFound.body, { status: 404, headers });
  }
  return next();
}
