CREATE TABLE sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    agency_org TEXT NOT NULL DEFAULT 'Federal Communications Commission',
    source_type TEXT NOT NULL,
    document_no TEXT,
    docket_no TEXT,
    publication_date TEXT,
    url TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    is_primary_source INTEGER NOT NULL DEFAULT 1 CHECK (is_primary_source IN (0,1)),
    reliability TEXT NOT NULL DEFAULT 'primary',
    summary TEXT,
    citation_hint TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    severity TEXT NOT NULL CHECK (severity IN ('info','notice','warning','urgent')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    starts_at TEXT,
    ends_at TEXT,
    cta_label TEXT,
    cta_url TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE api_examples (
    example_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    sql_query TEXT NOT NULL
);

CREATE TABLE audience_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE checklist_items (
    checklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audience_segment_id INTEGER NOT NULL REFERENCES audience_segments(segment_id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low','medium','high','urgent')),
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('true','false','mostly_true','mostly_false','mixed','unknown')),
    explanation TEXT NOT NULL,
    consumer_guidance TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE conditional_approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    producer TEXT NOT NULL,
    brand_or_product_family TEXT,
    device_description TEXT NOT NULL,
    device_series_or_models TEXT,
    approval_start_date TEXT NOT NULL,
    approval_end_date TEXT NOT NULL,
    granted_by TEXT NOT NULL DEFAULT 'Department of War (DoW)',
    status TEXT NOT NULL CHECK (status IN ('active','expired','superseded','unknown')),
    consumer_facing_note TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE consumer_faqs (
    faq_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_short TEXT NOT NULL,
    answer_long TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low','medium','high','informational')),
    last_verified_at TEXT NOT NULL
);

CREATE TABLE content_pages (
    page_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body_md TEXT NOT NULL,
    audience TEXT NOT NULL DEFAULT 'consumer',
    status TEXT NOT NULL CHECK (status IN ('draft','published','archived')) DEFAULT 'published',
    last_verified_at TEXT NOT NULL
);

CREATE TABLE content_page_sources (
    page_id INTEGER NOT NULL REFERENCES content_pages(page_id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    PRIMARY KEY (page_id, source_id)
);

CREATE TABLE covered_list_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    entry_text TEXT NOT NULL,
    added_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('current','superseded','proposed')),
    exemptions_text TEXT,
    scope_note TEXT,
    consumer_effect TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE data_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_type TEXT NOT NULL,
    note TEXT NOT NULL,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE definitions (
    definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    scope_note TEXT,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    last_verified_at TEXT NOT NULL
);

CREATE TABLE faq_sources (
    faq_id INTEGER NOT NULL REFERENCES consumer_faqs(faq_id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    PRIMARY KEY (faq_id, source_id)
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE regulatory_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    short_label TEXT,
    summary TEXT NOT NULL,
    consumer_impact TEXT,
    legal_effect TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    is_router_relevant INTEGER NOT NULL DEFAULT 1 CHECK (is_router_relevant IN (0,1)),
    display_order INTEGER NOT NULL DEFAULT 100
);

CREATE VIRTUAL TABLE search_index USING fts5(
    table_name UNINDEXED,
    row_id UNINDEXED,
    title,
    body,
    source_url UNINDEXED
);

CREATE TABLE update_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    frequency TEXT NOT NULL,
    instructions TEXT NOT NULL,
    last_checked TEXT,
    next_check_hint TEXT
);

CREATE TABLE waivers (
    waiver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    waiver_type TEXT NOT NULL,
    party TEXT NOT NULL,
    equipment_scope TEXT NOT NULL,
    changes_allowed TEXT NOT NULL,
    release_date TEXT NOT NULL,
    effective_start_date TEXT,
    effective_end_date TEXT,
    status TEXT NOT NULL CHECK (status IN ('active','expired','proposed','superseded','unknown')),
    limitations TEXT,
    consumer_impact TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    last_verified_at TEXT NOT NULL
);

CREATE INDEX idx_sources_publication_date ON sources(publication_date);

CREATE INDEX idx_sources_document_no ON sources(document_no);

CREATE INDEX idx_reg_events_date ON regulatory_events(event_date);

CREATE INDEX idx_reg_events_type ON regulatory_events(event_type);

CREATE INDEX idx_covered_status ON covered_list_entries(status);

CREATE INDEX idx_covered_added ON covered_list_entries(added_date);

CREATE INDEX idx_conditional_producer ON conditional_approvals(producer);

CREATE INDEX idx_conditional_dates ON conditional_approvals(approval_start_date, approval_end_date);

CREATE INDEX idx_conditional_status ON conditional_approvals(status);

CREATE INDEX idx_waivers_dates ON waivers(effective_start_date, effective_end_date);

CREATE INDEX idx_waivers_type ON waivers(waiver_type);

CREATE INDEX idx_waivers_status ON waivers(status);

CREATE INDEX idx_faq_order ON consumer_faqs(display_order);

CREATE INDEX idx_faq_category ON consumer_faqs(category);

CREATE INDEX idx_claims_verdict ON claims(verdict);

CREATE INDEX idx_checklist_segment_priority ON checklist_items(audience_segment_id, priority);

CREATE INDEX idx_alerts_active ON alerts(active, severity);

CREATE VIEW vw_current_consumer_status AS
SELECT
    (SELECT value FROM metadata WHERE key = 'current_as_of') AS current_as_of,
    'New foreign-produced consumer router models generally cannot receive FCC equipment authorization unless a Conditional Approval applies.' AS headline,
    'Existing previously authorized models and routers already purchased by consumers are not banned from continued use.' AS continued_use_note,
    'Software and firmware updates that mitigate harm for covered routers authorized before March 23, 2026 are covered by an FCC waiver through at least January 1, 2029.' AS update_note,
    'Check the current FCC Covered List and Conditional Approvals before publishing compliance statements.' AS verification_note;

CREATE VIEW vw_router_timeline AS
SELECT
    e.event_date,
    e.event_type,
    e.short_label,
    e.title,
    e.summary,
    e.consumer_impact,
    e.legal_effect,
    s.title AS source_title,
    s.document_no,
    s.url AS source_url
FROM regulatory_events e
JOIN sources s ON e.source_id = s.source_id
WHERE e.is_router_relevant = 1
ORDER BY e.event_date, e.display_order, e.event_id;

CREATE VIEW vw_active_conditional_approvals AS
SELECT
    ca.producer,
    ca.brand_or_product_family,
    ca.device_description,
    ca.device_series_or_models,
    ca.approval_start_date,
    ca.approval_end_date,
    CAST(julianday(ca.approval_end_date) - julianday((SELECT value FROM metadata WHERE key = 'current_as_of')) AS INTEGER) AS days_until_end_as_of_dataset,
    ca.consumer_facing_note,
    s.document_no,
    s.url AS source_url
FROM conditional_approvals ca
JOIN sources s ON ca.source_id = s.source_id
WHERE ca.status = 'active'
  AND ca.approval_end_date >= (SELECT value FROM metadata WHERE key = 'current_as_of')
ORDER BY ca.approval_end_date, ca.producer;

CREATE VIEW vw_expiring_soon_conditional_approvals AS
SELECT *
FROM vw_active_conditional_approvals
WHERE days_until_end_as_of_dataset <= 180;

CREATE VIEW vw_active_waivers AS
SELECT
    w.waiver_type,
    w.party,
    w.equipment_scope,
    w.changes_allowed,
    w.effective_start_date,
    w.effective_end_date,
    w.limitations,
    w.consumer_impact,
    s.document_no,
    s.url AS source_url
FROM waivers w
JOIN sources s ON w.source_id = s.source_id
WHERE w.status IN ('active','proposed')
  AND (w.effective_end_date IS NULL OR w.effective_end_date >= (SELECT value FROM metadata WHERE key = 'current_as_of'))
ORDER BY COALESCE(w.effective_end_date, '9999-12-31'), w.party;

CREATE VIEW vw_public_faqs AS
SELECT
    f.category,
    f.question,
    f.answer_short,
    f.answer_long,
    f.risk_level,
    GROUP_CONCAT(s.url, ' | ') AS source_urls
FROM consumer_faqs f
LEFT JOIN faq_sources fs ON f.faq_id = fs.faq_id
LEFT JOIN sources s ON fs.source_id = s.source_id
GROUP BY f.faq_id
ORDER BY f.display_order;

CREATE VIEW vw_primary_sources AS
SELECT
    source_key,
    title,
    source_type,
    document_no,
    publication_date,
    url,
    summary
FROM sources
WHERE is_primary_source = 1
ORDER BY publication_date, source_id;
