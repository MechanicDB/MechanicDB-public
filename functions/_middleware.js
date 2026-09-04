// Old Cloudflare Pages host -> canonical domain.
// Exact-host match so branch-preview hosts (<hash>.mechanicdb-public.pages.dev)
// and the custom domain itself are never redirected. Everything else falls
// through to the static assets (404.html, _headers, _redirects unchanged).
const OLD_HOST = "mechanicdb-public.pages.dev";
const NEW_HOST = "mechanicdb.dataengineered.io";

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === OLD_HOST) {
    url.hostname = NEW_HOST;
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
