---
name: frontend-seo
description: Audit and implement technical and on-page SEO improvements in any frontend project. Use when adding or fixing metadata, crawlability, structured data, sitemaps, performance, accessibility, URLs, or mobile SEO; not for inventing off-site links or accessing third-party accounts without authorization.
---

# Frontend SEO

Make the site easy for search engines and people to understand, crawl, and use. Work within the existing framework and deployment model; do not replace routing, design, analytics, or hosting merely to apply generic SEO patterns.

## Start with evidence

Identify the framework, route model (static, SSR, SSG, SPA), public URL, hosting/CDN configuration, and existing SEO implementation. Check representative pages and templates rather than applying a blind global change. Preserve intentional `noindex` directives, redirects, and canonical behavior until their purpose is understood.

When a public site or current platform behavior is relevant, inspect it and use authoritative framework, search-engine, or hosting documentation. For Core Web Vitals, measure a realistic production or preview page before and after a change when possible; distinguish lab results from field data.

## Implement the right layer

Prefer shared layouts, route metadata APIs, and reusable components for site-wide defaults, with route-level overrides for unique pages. Ensure rendered HTML contains the relevant SEO tags; client-only mutations are a fallback for SPAs, not the preferred implementation.

- Give every indexable page a concise, distinct `<title>` and meta description based on its actual content. Avoid keyword stuffing and duplicate boilerplate.
- Use exactly one meaningful `<h1>` per page. Correct heading order without using headings solely for visual styling.
- Add concise, context-appropriate `alt` text to informative images. Use empty `alt` for genuinely decorative images; do not duplicate nearby text or manufacture descriptions for unknown images.
- Generate stable, HTTPS canonical URLs from one trusted site-origin setting. Use self-referencing canonicals for preferred indexable URLs and do not canonicalize distinct content to an arbitrary page.
- Add complete Open Graph metadata, including an absolute `og:image` URL. Create or select a real, crawlable image with a suitable social-sharing aspect ratio; do not point to a missing asset.
- Add JSON-LD only when its facts are visible on the page and can be kept accurate. Choose schema types that fit the page (for example Organization, WebSite, BreadcrumbList, Article, Product, FAQPage where eligible). Do not fabricate ratings, reviews, offers, or FAQs.
- Build `robots.txt` and `sitemap.xml` from the canonical public routes. Exclude private, duplicate, error, redirected, search/filter, and `noindex` pages. Include the sitemap URL in `robots.txt`; add accurate `lastmod` only if it is reliably known.
- Keep public URLs lowercase, readable, stable, and hyphen-separated. Add permanent redirects for changed legacy URLs and update internal links; never silently break external or bookmarked URLs.
- Repair genuine broken internal links and add internal links where they materially help navigation and topical discovery. Do not add irrelevant link blocks or fake anchors.
- Enforce HTTPS at the hosting edge or application redirect layer, preserving paths and query strings. Do not make DNS, certificate, HSTS, or hosting changes without the user’s authorization and confirmed deployment context.

## Required SEO coverage

For every audit or implementation, explicitly check the following 19 areas and report any item that is not applicable, blocked, or intentionally deferred:

1. **`sitemap.xml`** — Generate it from canonical, public, indexable routes only.
2. **`robots.txt`** — Add it at the site root, avoid blocking assets or public pages needed for rendering and discovery, and reference the absolute sitemap URL.
3. **Remove unintended `noindex` tags** — Indexable pages must not emit `noindex` through HTML, HTTP headers, or framework configuration. Preserve `noindex` only for pages that are intentionally private, duplicate, transactional, or otherwise excluded from search.
4. **Canonical tags** — Emit one stable, self-referencing canonical for each preferred indexable URL, using the trusted HTTPS site origin.
5. **Meta titles** — Give each indexable page a distinct, concise, content-accurate `<title>`.
6. **Meta descriptions** — Give each indexable page a distinct, useful description; avoid duplicate boilerplate and keyword stuffing.
7. **One H1 per page** — Use exactly one meaningful `<h1>` on each indexable page.
8. **Header hierarchy** — Keep headings in a logical order (`h1` → `h2` → `h3`), without skipping levels for visual styling.
9. **Alt text** — Add concise, context-appropriate `alt` text to informative images and `alt=""` to genuinely decorative images.
10. **Schema markup** — Add accurate JSON-LD only for facts visible on the page; choose a schema type that fits the content and keep it current.
11. **Internal links** — Link related, useful pages with descriptive anchors where this improves navigation and topical discovery.
12. **Broken links** — Scan and repair genuine broken internal links; update links after URL changes and avoid fake or irrelevant anchors.
13. **Image compression** — Optimize image bytes with the existing pipeline while preserving required quality, transparency, animation, and art direction; retain originals unless replacement is authorized.
14. **Core Web Vitals** — Measure realistic production or preview pages, identify the actual bottleneck, and improve LCP, INP, and CLS with evidence-based changes.
15. **Mobile responsiveness** — Test narrow and wide viewports for layout, navigation, touch targets, overflow, text readability, and image behavior.
16. **HTTPS** — Enforce HTTPS while preserving paths and query strings; confirm the deployment context before changing hosting, certificates, HSTS, or redirects.
17. **URL slugs** — Keep public URLs lowercase, readable, stable, and hyphen-separated; add permanent redirects for changed legacy URLs.
18. **`llms.txt`** — Add a root-level `/llms.txt` when the site owner wants an AI-readable content guide; keep it concise, factual, maintained, and limited to public canonical resources. Do not expose private content or treat it as a substitute for `robots.txt`.
19. **Backlink strategy** — Produce a strategy based on the site’s real audience and link-worthy assets, including relevant partners or publications, ethical outreach angles, and measurable success criteria. Do not buy links, fabricate citations, spam third parties, or send outreach without approval.

## Performance and mobile

Improve the bottleneck found in measurement rather than accumulating speculative optimizations. Typical high-value work includes responsive image dimensions and `srcset`/`sizes`, modern image formats, appropriate compression, lazy-loading below-the-fold images, prioritized/LCP image loading, font subsetting and loading strategy, eliminating render-blocking work, code splitting, and avoiding layout shifts with reserved dimensions.

Compress or optimize source images only where it will not destroy required quality, transparency, animation, or art direction. Prefer the project’s existing image pipeline and retain originals unless the request explicitly authorizes replacement. Validate responsive layouts at narrow and wide viewports, including navigation, touch targets, overflow, readable text, and image behavior.

## External and strategic items

For Search Console, prepare verification instructions or configuration assets appropriate to the confirmed verification method. Completing verification requires the site owner’s account and authorization; do not claim it is verified unless it is.

Provide a backlink strategy grounded in the site’s real audience and assets: identify link-worthy pages, relevant partners/publications/directories, outreach angles, and how success will be measured. Never buy links, fabricate citations, spam third parties, or send outreach without explicit approval.

If adding `llms.txt`, keep it limited to a maintained index of public, canonical resources and useful context for AI systems. It is an optional content-discovery aid, not an access-control mechanism and not a replacement for `robots.txt`.

## Validate before handoff

Build the project and run its relevant tests or checks. Inspect representative rendered page source for title, description, canonical, robots, Open Graph, heading, image alt, and JSON-LD output. Fetch or inspect `/robots.txt` and `/sitemap.xml`, check sitemap URLs resolve as intended, scan changed routes for broken internal links, and test redirects when URL changes were made. Report what changed, what was measured, and any remaining ownership-dependent steps.
