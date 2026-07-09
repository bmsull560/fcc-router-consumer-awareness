# FCC Router Consumer Awareness Database

Generated: 2026-07-09T18:53:42Z  
Current as of: 2026-07-09  
Format: SQLite 3 database plus SQL dump

## Purpose

This package is designed to power a consumer-awareness website about the FCC Covered List action involving routers produced in foreign countries. It includes source-backed, normalized data for:

- FCC primary sources
- regulatory timeline
- covered-list entry language
- consumer FAQs
- claims/myth checks
- router Conditional Approvals
- software/firmware and hardware waivers
- website alerts
- content-page starter copy
- update jobs and freshness notes

## Files

- `fcc_router_consumer_awareness.db` - SQLite database
- `fcc_router_consumer_awareness.sql` - full SQL dump
- `fcc_router_consumer_awareness_README.md` - this file

## Key tables

| Table | Purpose |
|---|---|
| `sources` | Primary FCC source documents and live page pointer |
| `regulatory_events` | Timeline of Covered List, waivers, approvals, and proposed rules |
| `covered_list_entries` | Router covered-list entry and consumer effect |
| `definitions` | Glossary terms for explainers |
| `conditional_approvals` | Product/family-scoped time-limited Conditional Approvals |
| `waivers` | Software/firmware and hardware waiver data |
| `consumer_faqs` + `faq_sources` | Public FAQ content with source mapping |
| `claims` | Myth-check or claim-verdict content |
| `audience_segments` + `checklist_items` | Consumer/retailer/ISP/journalist/web-admin checklist items |
| `alerts` | Site banners and warnings |
| `content_pages` + `content_page_sources` | Starter Markdown pages |
| `api_examples` | Ready-to-use query examples |
| `update_jobs` | Maintenance workflow recommendations |
| `data_notes` | Scope, caveats, and freshness notes |

## Useful views

| View | Use |
|---|---|
| `vw_current_consumer_status` | One-row homepage status panel |
| `vw_router_timeline` | Timeline page |
| `vw_active_conditional_approvals` | Current approvals table as of dataset date |
| `vw_expiring_soon_conditional_approvals` | Approvals ending within 180 days |
| `vw_active_waivers` | Active/proposed waivers |
| `vw_public_faqs` | FAQ page with source URLs |
| `vw_primary_sources` | Sources page |

## Example queries

```sql
-- Homepage status
SELECT * FROM vw_current_consumer_status;

-- Timeline
SELECT * FROM vw_router_timeline;

-- Conditional approvals
SELECT * FROM vw_active_conditional_approvals;

-- FAQs
SELECT category, question, answer_short, answer_long, source_urls
FROM vw_public_faqs;

-- Myth checks
SELECT claim, verdict, explanation, consumer_guidance
FROM claims
ORDER BY claim_id;

-- Active alerts
SELECT severity, title, body, cta_label, cta_url
FROM alerts
WHERE active = 1
ORDER BY CASE severity
  WHEN 'urgent' THEN 1
  WHEN 'warning' THEN 2
  WHEN 'notice' THEN 3
  ELSE 4
END;
```

## FTS search

If your SQLite build supports FTS5, this package includes `search_index`.

```sql
SELECT table_name, row_id, title,
       snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
FROM search_index
WHERE search_index MATCH 'firmware OR updates';
```

## Validation

SQLite integrity check at generation time: `ok`

Row counts:

```json
{
  "sources": 18,
  "regulatory_events": 15,
  "covered_list_entries": 1,
  "definitions": 6,
  "conditional_approvals": 11,
  "waivers": 8,
  "consumer_faqs": 7,
  "claims": 6,
  "audience_segments": 5,
  "checklist_items": 10,
  "alerts": 4,
  "content_pages": 5,
  "api_examples": 8,
  "update_jobs": 5,
  "data_notes": 6
}
```

View counts:

```json
{
  "vw_current_consumer_status": 1,
  "vw_router_timeline": 15,
  "vw_active_conditional_approvals": 11,
  "vw_expiring_soon_conditional_approvals": 0,
  "vw_active_waivers": 7,
  "vw_public_faqs": 7,
  "vw_primary_sources": 18
}
```

FTS5 search_index created: `True`

## Important caveats

This database is educational and not legal advice. It is not a complete product SKU compliance database and does not replace checking the live FCC Covered List, Conditional Approvals, or FCC Equipment Authorization records. Refresh this data before publishing compliance-sensitive claims.
