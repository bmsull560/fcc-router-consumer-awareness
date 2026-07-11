# ADR 001: Static-site generator architecture

## Status

Accepted

## Context

The site needs to be cheap to host, easy to cache, and resilient to database outages. It is informational and not a live transactional system.

## Decision

Generate static HTML, CSS, and JSON from the SQLite database during a build step, then serve the resulting files from any static host (GitHub Pages, S3, CDN).

- Python stdlib + Jinja-like `string.Template` keeps tooling minimal.
- A tiny SQLite API (`app/sqlite_api.py`) remains available for local development and API consumers.
- Client-side search fetches a pre-built `search_index.json` so no server-side search is required in production.

## Consequences

- **Pros**: simple deployment, no runtime DB dependency for readers, fast page loads, easy CDN caching.
- **Cons**: content is stale until the next build; the build must be re-run after database updates. This is acceptable because regulatory data changes infrequently and the site shows a `current_as_of` date.

## Alternatives considered

- Dynamic Flask/Django app: adds operational complexity and runtime cost for an informational site.
- Server-side rendering on every request: unnecessary for mostly-static regulatory content.
