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

// Repo-only files. Pages serves the whole repository root, so without this the
// translation catalogs, the build scripts, their config, the README and dotfiles
// would be downloadable from the site. They get the site's normal 404 instead
// (they stay in the GitHub repository).
const REPO_ONLY_PREFIXES = ["/locales/", "/scripts/"];
const REPO_ONLY_FILES = new Set(["/i18n.config.json", "/readme.md", "/vercel.json", "/requirements.txt"]);

// Matched on the decoded, slash-collapsed, lower-cased path, because the asset
// server also answers /locales%2Fes.json and //locales/es.json.
function isRepoOnly(pathname) {
  let path;
  try {
    path = decodeURIComponent(pathname);
  } catch {
    return true; // malformed escapes never name a real page
  }
  path = path.replace(/\/{2,}/g, "/").toLowerCase();
  if (REPO_ONLY_FILES.has(path)) return true;
  if (REPO_ONLY_PREFIXES.some((prefix) => path.startsWith(prefix))) return true;
  // dotfiles and dot-segments (.gitignore, .github/, ..), but keep /.well-known/ usable
  return path.split("/").some((seg) => seg.startsWith(".") && seg !== ".well-known");
}

export async function onRequest({ request, env, next }) {
  const url = new URL(request.url);
  if (url.hostname === OLD_HOST) {
    url.hostname = NEW_HOST;
    return Response.redirect(url.toString(), 301);
  }
  if (isRepoOnly(url.pathname)) {
    // A path that cannot exist makes Pages answer with 404.html, as for any unknown URL.
    const missing = await env.ASSETS.fetch(new URL("/__not_found__", url).toString());
    return new Response(missing.body, { status: 404, headers: missing.headers });
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
