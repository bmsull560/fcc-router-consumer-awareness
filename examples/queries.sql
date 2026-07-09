-- Useful website/API queries for the FCC router consumer-awareness database.

-- Homepage status
SELECT * FROM vw_current_consumer_status;

-- Regulatory timeline
SELECT event_date, event_type, title, summary, source_title, source_url
FROM vw_router_timeline
ORDER BY event_date DESC;

-- Public FAQs
SELECT category, question, answer_short, answer_long, source_urls
FROM vw_public_faqs
ORDER BY category, question;

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
END, alert_id;

-- Active Conditional Approvals
SELECT producer, brand_or_product_family, device_description, approval_start_date, approval_end_date, source_url
FROM vw_active_conditional_approvals
ORDER BY approval_end_date, producer;

-- Active/proposed waivers
SELECT waiver_type, party, equipment_scope, effective_start_date, effective_end_date, source_url
FROM vw_active_waivers
ORDER BY effective_end_date, party;

-- Primary source library
SELECT publication_date, title, source_type, url
FROM vw_primary_sources
ORDER BY publication_date DESC, source_key DESC;

-- FTS5 site search example
SELECT table_name, row_id, title,
       snippet(search_index, 3, '<mark>', '</mark>', '...', 16) AS snippet
FROM search_index
WHERE search_index MATCH 'firmware OR updates'
LIMIT 20;
