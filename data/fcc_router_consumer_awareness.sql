BEGIN TRANSACTION;
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
INSERT INTO "alerts" VALUES(1,'notice','Dataset current as of July 9, 2026','This database includes FCC materials through the July 7, 2026 Covered List update. Verify the live FCC Covered List before publication.','2026-07-09',NULL,'Open FCC Covered List','https://www.fcc.gov/supplychain/coveredlist',1,18,'2026-07-09');
INSERT INTO "alerts" VALUES(2,'info','Router software and firmware updates remain allowed for covered routers under waiver','Already-authorized covered routers may continue to receive software and firmware updates that mitigate harm through at least January 1, 2029.','2026-05-08','2029-01-01','Read FCC waiver','https://docs.fcc.gov/public/attachments/DA-26-454A1.pdf',1,4,'2026-07-09');
INSERT INTO "alerts" VALUES(3,'warning','Conditional Approvals are time-limited','Use the conditional_approvals table to show approval end dates; do not imply a permanent exemption.','2026-07-09',NULL,'See active approvals',NULL,1,10,'2026-07-09');
INSERT INTO "alerts" VALUES(4,'warning','Proposed component rules are not final','The July 1 FCC item includes proposals. Label that content as proposed until a final order is adopted.','2026-07-01',NULL,'Read proposal','https://docs.fcc.gov/public/attachments/DOC-422746A1.pdf',1,16,'2026-07-09');
CREATE TABLE api_examples (
    example_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    sql_query TEXT NOT NULL
);
INSERT INTO "api_examples" VALUES(1,'homepage_status','One-row status banner for the website homepage.','SELECT * FROM vw_current_consumer_status;');
INSERT INTO "api_examples" VALUES(2,'timeline','Chronological router regulatory timeline.','SELECT * FROM vw_router_timeline;');
INSERT INTO "api_examples" VALUES(3,'active_conditional_approvals','Active router Conditional Approvals as of the dataset date.','SELECT * FROM vw_active_conditional_approvals;');
INSERT INTO "api_examples" VALUES(4,'expiring_approvals','Approvals expiring within 180 days of the dataset date.','SELECT * FROM vw_expiring_soon_conditional_approvals;');
INSERT INTO "api_examples" VALUES(5,'faqs','Public FAQ content with source URLs.','SELECT category, question, answer_short, answer_long, source_urls FROM vw_public_faqs;');
INSERT INTO "api_examples" VALUES(6,'waivers','Active/proposed waivers to explain updates and supply-chain exceptions.','SELECT * FROM vw_active_waivers;');
INSERT INTO "api_examples" VALUES(7,'myth_checks','Claims and verdicts for misinformation sections.','SELECT claim, verdict, explanation, consumer_guidance FROM claims ORDER BY claim_id;');
INSERT INTO "api_examples" VALUES(8,'site_search','Search FTS content if FTS5 is available.','SELECT table_name, row_id, title, snippet(search_index, 3, ''<mark>'', ''</mark>'', ''...'', 16) AS snippet FROM search_index WHERE search_index MATCH ''firmware OR updates'';');
CREATE TABLE audience_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT
);
INSERT INTO "audience_segments" VALUES(1,'consumer','Consumers','People who own, buy, or use home routers.');
INSERT INTO "audience_segments" VALUES(2,'retailer','Retailers and marketplaces','Websites and stores describing availability or compliance of router products.');
INSERT INTO "audience_segments" VALUES(3,'isp','Internet service providers','Providers that supply or manage routers for subscribers.');
INSERT INTO "audience_segments" VALUES(4,'journalist','Journalists and researchers','People explaining the rule to the public.');
INSERT INTO "audience_segments" VALUES(5,'web_admin','Website administrators','People operating the consumer awareness website powered by this database.');
CREATE TABLE checklist_items (
    checklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audience_segment_id INTEGER NOT NULL REFERENCES audience_segments(segment_id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low','medium','high','urgent')),
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    last_verified_at TEXT NOT NULL
);
INSERT INTO "checklist_items" VALUES(1,1,'Check whether your router still receives firmware updates from the manufacturer or ISP.','Updates are the main way known vulnerabilities are fixed.','high',4,'2026-07-09');
INSERT INTO "checklist_items" VALUES(2,1,'Do not discard a working router solely because it was manufactured abroad.','The FCC said previously purchased consumer-grade routers are not affected by continued-use prohibitions.','medium',1,'2026-07-09');
INSERT INTO "checklist_items" VALUES(3,1,'Use a strong admin password and disable unnecessary remote administration.','The FCC action is separate from everyday router hygiene; consumers still need basic security practices.','medium',4,'2026-07-09');
INSERT INTO "checklist_items" VALUES(4,2,'Separate product pages for previously authorized existing models from pages for future/new models.','The legal posture can differ by authorization status and Conditional Approval scope.','high',1,'2026-07-09');
INSERT INTO "checklist_items" VALUES(5,2,'Display Conditional Approval dates and covered product families where you make compliance claims.','Approvals are time-limited and scope-specific.','urgent',10,'2026-07-09');
INSERT INTO "checklist_items" VALUES(6,3,'Map each deployed router SKU to FCC authorization status and Conditional Approval or waiver coverage.','Consumer communications should be model-specific where possible.','urgent',18,'2026-07-09');
INSERT INTO "checklist_items" VALUES(7,3,'Keep firmware-update channels active for covered routers authorized before March 23, 2026.','OET''s waiver is intended to keep updates that mitigate harm flowing to consumers.','high',4,'2026-07-09');
INSERT INTO "checklist_items" VALUES(8,4,'Avoid headlines that say all foreign-made routers are banned.','The FCC action does not ban already-purchased routers and does not ban sale/use of previously authorized existing models.','high',1,'2026-07-09');
INSERT INTO "checklist_items" VALUES(9,5,'Refresh the FCC Covered List and Conditional Approvals before publishing current model guidance.','The list and approvals can change without this static database updating itself.','urgent',18,'2026-07-09');
INSERT INTO "checklist_items" VALUES(10,5,'Track approval and waiver expiration dates with automated alerts.','Consumer-facing claims become stale when approvals or waivers expire.','high',10,'2026-07-09');
CREATE TABLE claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('true','false','mostly_true','mostly_false','mixed','unknown')),
    explanation TEXT NOT NULL,
    consumer_guidance TEXT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    last_verified_at TEXT NOT NULL
);
INSERT INTO "claims" VALUES(1,'The FCC banned consumers from using routers they already own.','false','The FCC fact sheet says the update does not affect previously purchased consumer-grade routers.','Do not tell consumers to throw away working routers solely because of the Covered List update.',1,'2026-07-09');
INSERT INTO "claims" VALUES(2,'New foreign-produced consumer router models generally cannot get FCC authorization unless conditionally approved.','mostly_true','FCC materials say covered equipment is prohibited from getting new equipment authorization and that the router entry excludes routers with Conditional Approval by DoW or DHS.','Add the caveat that existing authorized models and conditional approvals are different from new covered models.',17,'2026-07-09');
INSERT INTO "claims" VALUES(3,'Retailers can keep selling existing router models already authorized by the FCC.','true','The FCC fact sheet says the update does not prohibit import, sale, or use of any existing device models previously authorized.','A product page should still avoid claiming every unit is unaffected without verifying the model authorization status.',1,'2026-07-09');
INSERT INTO "claims" VALUES(4,'Firmware updates are banned for foreign-produced routers.','false','OET extended and expanded a waiver allowing software and firmware updates that mitigate harm for certain already-authorized covered routers through at least January 1, 2029.','Encourage consumers to apply legitimate updates from vendors or ISPs.',4,'2026-07-09');
INSERT INTO "claims" VALUES(5,'A Conditional Approval is permanent.','false','The conditional approvals listed in this database have start and end dates and apply only to specified devices or product families.','Show approval dates and model scope prominently on your site.',10,'2026-07-09');
INSERT INTO "claims" VALUES(6,'Hardware changes to covered routers are generally treated differently from software/firmware updates.','true','FCC waiver orders repeatedly distinguish the broad software/firmware waiver from hardware changes, which generally remain prohibited unless covered by a separate waiver.','Do not imply hardware substitutions are broadly allowed; cite any specific waiver.',12,'2026-07-09');
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
INSERT INTO "conditional_approvals" VALUES(1,'Netgear, Inc.','Nighthawk / Orbi / cable gateways and modems','Nighthawk consumer mesh routers, mobile routers, and standalone routers; Orbi consumer mesh routers, mobile routers, and standalone routers; cable gateways and cable modems.','Nighthawk R, RAX, RAXE, RS, MK, MR, M, MH series; Orbi RBK, RBE, RBR, RBRE, LBR, LBK, CBK series; CAX cable gateways; CM cable modems.','2026-04-14','2027-10-01','Department of War (DoW)','active','Scope is limited to the listed product families and the stated approval period.',5,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(2,'Adtran, Inc.','Service Delivery Gateway (SDG)','Service Delivery Gateway class routers.','SDG class routers.','2026-04-14','2027-10-01','Department of War (DoW)','active','Scope is limited to SDG class routers and the stated approval period.',5,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(3,'eero LLC','eero / Amazon Leo','eero routers and Amazon Leo routers.','eero; eero Pro; eero Max; eero PoE; eero Outdoor; eero Signal; Amazon Leo routers.','2026-04-22','2027-10-31','Department of War (DoW)','active','Scope is limited to listed eero/Amazon Leo product families and the stated approval period.',6,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(4,'Calix, Inc.','Calix 7u6.2','Calix 7u6.2 router.','Part number 100-06200.','2026-05-06','2027-10-31','Department of War (DoW)','active','Scope is limited to Calix 7u6.2 router part number 100-06200 and the stated approval period.',7,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(5,'Nokia Corporation','Wireless-Fidelity 8','Nokia Wireless-Fidelity 8 router.','Wireless-Fidelity 8.','2026-05-15','2027-10-31','Department of War (DoW)','active','Scope is limited to Wireless-Fidelity 8 and the stated approval period.',7,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(6,'Nokia Corporation','Beacons / ONT Based Beacons / Fastmile Gateway','Nokia Beacons, Open Network Terminal (ONT) Based Beacons, and Fastmile Gateway routers.','Beacons; ONT Based Beacons; Fastmile Gateway routers.','2026-05-18','2027-10-31','Department of War (DoW)','active','Scope is limited to listed Nokia router families and the stated approval period.',7,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(7,'Calix, Inc.','Calix broadband routers','Calix broadband routers.','7p6; 7u6m.2; 7u4txg; 7u4.','2026-06-01','2027-11-22','Department of War (DoW)','active','Scope is limited to listed Calix broadband routers and the stated approval period.',7,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(8,'Alpha Networks Inc. USA','Alpha Networks 1700/2700','Alpha Networks router series.','1700 series; 2700 series.','2026-06-01','2027-11-22','Department of War (DoW)','active','Scope is limited to listed Alpha Networks router series and the stated approval period.',7,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(9,'Sagemcom USA LLC','FAST routers','Sagemcom USA FAST routers.','FAST3994; FAST3897; FAST5698; FAST5699; FAST5999.','2026-06-04','2027-12-05','Department of War (DoW)','active','Scope is limited to listed FAST routers and the stated approval period.',8,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(10,'Miri Technologies, Inc.','Miri X10','Miri X10 Travel router.','Miri X10 Travel router.','2026-06-12','2027-12-12','Department of War (DoW)','active','Scope is limited to the Miri X10 Travel router and the stated approval period.',9,'2026-07-09');
INSERT INTO "conditional_approvals" VALUES(11,'Arcadyan Technology Corporation','T-Mobile / AT&T / Verizon router devices','Arcadyan routers for T-Mobile 5G FWA broadband devices; AT&T BGW 720; Verizon devices.','T-Mobile 5G FWA devices including G5AR, G5MAR, GxMAR, GxMAR-ODU, GxAR Series (5G FWA); AT&T BGW 720; Verizon C46BE (XC Series), CR100B (WG Series), CE1000A, E3200 (WE Series).','2026-06-12','2027-12-12','Department of War (DoW)','active','Scope is limited to listed T-Mobile, AT&T, and Verizon device families/models and the stated approval period.',10,'2026-07-09');
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
INSERT INTO "consumer_faqs" VALUES(1,'Basics','Are all foreign-made routers now illegal to own?','No. The FCC said the March 23, 2026 update does not affect previously purchased consumer-grade routers.','The rule change targets new covered router models and FCC equipment authorization. Consumers can continue to use routers they already lawfully purchased or acquired. Retailers can also continue to sell, import, or market router models that were previously approved through FCC equipment authorization.',10,'low','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(2,'Buying','Can I still buy a router that was made outside the United States?','Yes, if it is an existing model previously authorized by the FCC or a model with a valid Conditional Approval.','The consumer-friendly rule of thumb is: previously authorized existing models are not banned by this update, while new foreign-produced covered router models generally need a Conditional Approval route before they can be authorized, imported, marketed, or sold.',20,'medium','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(3,'Updates','Should I keep installing router firmware updates?','Yes. Use legitimate updates from the router maker or your ISP.','The FCC/OET extended and expanded a waiver so already-authorized covered routers may continue receiving software and firmware updates that mitigate harm through at least January 1, 2029. This includes updates that maintain functionality, patch vulnerabilities, or support compatibility.',30,'low','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(4,'Approvals','What is a Conditional Approval?','It is a time-limited exemption for specific devices or device families.','A Conditional Approval means DoW or DHS determined that the specified router device or class of devices does not pose unacceptable risks for the stated scope and dates. It is not necessarily a permanent clearance for all products made by that company.',40,'medium','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(5,'ISP equipment','What if my router came from my internet provider?','You can keep using it, but check for notices from the provider about replacement or firmware updates.','ISP-supplied routers may be affected by the same Covered List framework, but some providers and suppliers have received limited hardware waivers or Conditional Approvals. Consumers should not unplug or discard working equipment solely because it was manufactured abroad.',50,'medium','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(6,'Safety','Does Conditional Approval mean a router is guaranteed secure?','No. It is a national-security Covered List determination, not a consumer security guarantee.','Consumers should still use normal router safety practices: install updates, use strong Wi-Fi passwords, disable unnecessary remote administration, and replace end-of-life products that no longer receive updates.',60,'medium','2026-07-09');
INSERT INTO "consumer_faqs" VALUES(7,'Website data','How often should this site update its router data?','At least weekly, and immediately after FCC Covered List updates.','The FCC maintains a live Covered List and Conditional Approvals page. This database has a current-as-of date and should be refreshed before publication of any compliance-sensitive claims.',70,'high','2026-07-09');
CREATE TABLE content_page_sources (
    page_id INTEGER NOT NULL REFERENCES content_pages(page_id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    PRIMARY KEY (page_id, source_id)
);
INSERT INTO "content_page_sources" VALUES(1,1);
INSERT INTO "content_page_sources" VALUES(1,17);
INSERT INTO "content_page_sources" VALUES(1,4);
INSERT INTO "content_page_sources" VALUES(2,1);
INSERT INTO "content_page_sources" VALUES(2,18);
INSERT INTO "content_page_sources" VALUES(3,10);
INSERT INTO "content_page_sources" VALUES(3,18);
INSERT INTO "content_page_sources" VALUES(4,4);
INSERT INTO "content_page_sources" VALUES(5,1);
INSERT INTO "content_page_sources" VALUES(5,2);
INSERT INTO "content_page_sources" VALUES(5,4);
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
INSERT INTO "content_pages" VALUES(1,'home','What the FCC router action means for consumers','A plain-English landing page for consumers and router buyers.','# What changed

The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS.

# What did not change

You can continue using a router you already lawfully purchased or acquired. Previously authorized existing router models are not prohibited by the March 23 update.

# What to do now

Keep installing legitimate software and firmware updates. Check whether your router maker or internet provider still supports your model. For new purchases, prefer sellers that can identify FCC authorization status or a valid Conditional Approval when relevant.','consumer','published','2026-07-09');
INSERT INTO "content_pages" VALUES(2,'buying-guide','Router buying guide after the FCC Covered List update','Guidance for consumers considering a new router purchase.','# Buying checklist

1. Confirm the product is an existing FCC-authorized model or is covered by a valid Conditional Approval.
2. Check the manufacturer''s support page for firmware update history.
3. Avoid unsupported/end-of-life models even if they are legal to use.
4. Keep receipts and model numbers; approvals and support status are model-specific.

# Important caveat

This database is educational. It does not replace checking the live FCC Covered List or the FCC Equipment Authorization database for a specific product.','consumer','published','2026-07-09');
INSERT INTO "content_pages" VALUES(3,'conditional-approvals','Current router Conditional Approvals in this dataset','Explains and lists active Conditional Approvals.','# Conditional Approvals

Conditional Approval is a scoped, time-limited exemption. The same company may have approved and unapproved products, so product family and model details matter.

Use the `vw_active_conditional_approvals` view to render a current table and include approval end dates.','all','published','2026-07-09');
INSERT INTO "content_pages" VALUES(4,'updates','Firmware and software updates for existing routers','Explains why consumers should keep updating routers.','# Updates are still important

OET extended and expanded a waiver through at least January 1, 2029 for software and firmware updates that mitigate harm for covered routers authorized before March 23, 2026.

That means your site should not tell consumers to avoid updates. Instead, guide them toward legitimate updates from manufacturers or ISPs.','consumer','published','2026-07-09');
INSERT INTO "content_pages" VALUES(5,'retailer-notes','Notes for retailers and marketplaces','Short guidance for product-page compliance language.','# Retailer guidance

Avoid broad statements such as "all foreign-made routers are banned" or "all products from this brand are exempt."

Safer product-page language should distinguish:
- previously authorized existing models,
- new models,
- Conditional Approval scope,
- approval or waiver expiration dates,
- whether the claim is about sale/import/marketing, use, firmware updates, or hardware changes.','retailer','published','2026-07-09');
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
INSERT INTO "covered_list_entries" VALUES(1,'consumer routers','Routers produced in a foreign country, except routers which have been granted a Conditional Approval by DoW or DHS.','2026-03-23','current','Routers with Conditional Approval by DoW or DHS are excluded from the covered router entry for the approval period and scope.','The FCC documents define routers by reference to NIST IR 8425A to include consumer-grade networking devices primarily intended for residential use and installable by the customer.','New covered router models generally cannot receive FCC equipment authorization; previously authorized existing device models and previously purchased routers are not prohibited by the update.',17,'2026-07-09');
CREATE TABLE data_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_type TEXT NOT NULL,
    note TEXT NOT NULL,
    last_verified_at TEXT NOT NULL
);
INSERT INTO "data_notes" VALUES(1,'scope','This database is focused on consumer awareness and does not attempt to replicate the FCC Equipment Authorization database.','2026-07-09');
INSERT INTO "data_notes" VALUES(2,'legal','This database is not legal advice. Review all consumer-facing compliance claims with qualified counsel before publication.','2026-07-09');
INSERT INTO "data_notes" VALUES(3,'refresh','The FCC Covered List and Conditional Approvals can change. The current_as_of metadata value is the freshness boundary for this data.','2026-07-09');
INSERT INTO "data_notes" VALUES(4,'naming','The terms DoW and DHS follow the FCC source documents used in this data set.','2026-07-09');
INSERT INTO "data_notes" VALUES(5,'models','Conditional approval model-family rows are based on public FCC descriptions and may need SKU-level mapping before use in retail product pages.','2026-07-09');
INSERT INTO "data_notes" VALUES(6,'source_priority','Use primary FCC sources first. Secondary news coverage was not used to seed the database.','2026-07-09');
CREATE TABLE definitions (
    definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    scope_note TEXT,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    last_verified_at TEXT NOT NULL
);
INSERT INTO "definitions" VALUES(1,'Covered List','A list of communications equipment and services deemed to pose an unacceptable risk to U.S. national security or to the safety and security of U.S. persons.','For this database, the relevant entry is the router category added March 23, 2026.',1,'2026-07-09');
INSERT INTO "definitions" VALUES(2,'Covered Router','A router produced in a foreign country that falls within the FCC Covered List entry unless a Conditional Approval applies.','Used here as a consumer-facing shorthand; verify the official Covered List wording.',2,'2026-07-09');
INSERT INTO "definitions" VALUES(3,'Conditional Approval','A time-limited, scope-specific determination by DoW or DHS that identified devices do not pose unacceptable risks and are excluded from the Covered List for the stated period.','Approvals are not blanket approvals for all products from a company unless the approval specifically says so.',10,'2026-07-09');
INSERT INTO "definitions" VALUES(4,'Equipment Authorization','FCC authorization required for many electronic devices, including consumer-grade routers, before importation, marketing, or sale in the United States.','New covered equipment is prohibited from getting FCC equipment authorization.',1,'2026-07-09');
INSERT INTO "definitions" VALUES(5,'Permissive Change','A modification to already-authorized equipment under FCC rules. In this context, software and firmware updates may qualify as Class I or Class II permissive changes.','The DA 26-454 waiver applies to software/firmware updates that mitigate harm, but hardware changes generally require separate waivers.',4,'2026-07-09');
INSERT INTO "definitions" VALUES(6,'Already-authorized model','A router model that had received FCC authorization before the relevant Covered List addition.','The FCC fact sheet states the March 23 update does not prohibit import, sale, or use of previously authorized existing device models.',1,'2026-07-09');
CREATE TABLE faq_sources (
    faq_id INTEGER NOT NULL REFERENCES consumer_faqs(faq_id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    PRIMARY KEY (faq_id, source_id)
);
INSERT INTO "faq_sources" VALUES(1,1);
INSERT INTO "faq_sources" VALUES(1,17);
INSERT INTO "faq_sources" VALUES(2,1);
INSERT INTO "faq_sources" VALUES(2,2);
INSERT INTO "faq_sources" VALUES(3,4);
INSERT INTO "faq_sources" VALUES(4,2);
INSERT INTO "faq_sources" VALUES(4,10);
INSERT INTO "faq_sources" VALUES(5,1);
INSERT INTO "faq_sources" VALUES(5,12);
INSERT INTO "faq_sources" VALUES(5,14);
INSERT INTO "faq_sources" VALUES(6,10);
INSERT INTO "faq_sources" VALUES(6,4);
INSERT INTO "faq_sources" VALUES(7,18);
INSERT INTO "faq_sources" VALUES(7,17);
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT INTO "metadata" VALUES('db_name','FCC Router Consumer Awareness Database');
INSERT INTO "metadata" VALUES('db_version','1.0.0');
INSERT INTO "metadata" VALUES('current_as_of','2026-07-09');
INSERT INTO "metadata" VALUES('generated_at','2026-07-09T18:53:42Z');
INSERT INTO "metadata" VALUES('topic','FCC Covered List update for routers produced in foreign countries and consumer-facing impacts');
INSERT INTO "metadata" VALUES('license_note','Generated by ChatGPT from public FCC sources; review before publication.');
INSERT INTO "metadata" VALUES('not_legal_advice','This data set is educational and not legal advice.');
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
INSERT INTO "regulatory_events" VALUES(1,'2026-03-23','covered_list_update','Foreign-produced routers added to FCC Covered List','Router Covered List entry','The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS.','New covered router models generally cannot enter the U.S. market through new FCC equipment authorization unless conditionally approved.','Covered equipment is prohibited from receiving new FCC equipment authorizations; most consumer-grade routers require authorization before import/marketing/sale.',2,1,10);
INSERT INTO "regulatory_events" VALUES(2,'2026-03-23','consumer_guidance','FCC explains impact on consumers and retailers','Consumer impact guidance','The FCC fact sheet says existing authorized router models and previously purchased routers are not prohibited by the update.','Consumers may continue to use already-purchased routers; retailers may continue selling previously authorized models.','Restrictions apply to new device models on the Covered List.',1,1,20);
INSERT INTO "regulatory_events" VALUES(3,'2026-03-23','waiver','Initial software/firmware update waiver for covered routers','Initial update waiver','OET announced a waiver allowing certain Class I permissive software and firmware changes for already-authorized covered routers.','Reduced risk that already-deployed routers would stop receiving security-related updates immediately after the Covered List update.','Initial waiver later extended and expanded by DA 26-454.',3,1,30);
INSERT INTO "regulatory_events" VALUES(4,'2026-04-14','conditional_approval','Netgear and Adtran router Conditional Approvals','First router approvals','FCC reflected DoW Conditional Approvals for specified Netgear and Adtran router product families.','Certain specified foreign-produced router families were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',5,1,40);
INSERT INTO "regulatory_events" VALUES(5,'2026-04-22','conditional_approval','eero router Conditional Approvals','eero approvals','FCC reflected Conditional Approvals for eero/Amazon Leo router families.','Specified eero/Amazon Leo routers were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',6,1,50);
INSERT INTO "regulatory_events" VALUES(6,'2026-05-08','waiver','Software/firmware waiver extended and expanded through at least January 1, 2029','Update waiver extension','OET extended the software/firmware update waiver to at least January 1, 2029 and expanded it to analogous Class II permissive changes.','Already-authorized covered routers may continue to receive functionality, compatibility, and security updates that mitigate harm.','Applies to Class I and Class II software/firmware changes that mitigate harm; does not generally cover hardware changes.',4,1,60);
INSERT INTO "regulatory_events" VALUES(7,'2026-05-15','hardware_waiver','AT&T limited hardware-change waiver','AT&T waiver','OET granted AT&T a limited waiver for targeted hardware changes to existing authorized covered routers.','Helps avoid supply disruptions for affected broadband equipment.','Limited waiver; not a general authorization for new foreign-produced covered router models.',11,1,70);
INSERT INTO "regulatory_events" VALUES(8,'2026-05-15','conditional_approval','Nokia router Conditional Approvals','Nokia approvals','FCC reflected Conditional Approvals for specified Nokia router products.','Specified Nokia router products were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',7,1,80);
INSERT INTO "regulatory_events" VALUES(9,'2026-06-01','conditional_approval','Calix and Alpha Networks router Conditional Approvals','Calix/Alpha approvals','FCC reflected Conditional Approvals for specified Calix and Alpha Networks router products.','Specified Calix and Alpha Networks routers were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',7,1,90);
INSERT INTO "regulatory_events" VALUES(10,'2026-06-04','conditional_approval','Sagemcom FAST router Conditional Approvals','Sagemcom approvals','FCC reflected Conditional Approvals for Sagemcom USA FAST3994, FAST3897, FAST5698, FAST5699, and FAST5999 routers.','Specified Sagemcom routers were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',8,1,100);
INSERT INTO "regulatory_events" VALUES(11,'2026-06-09','hardware_waiver','NCTA and Sercomm limited hardware-change waivers','NCTA/Sercomm waivers','OET granted limited waivers involving specified hardware substitutions or end-of-life component changes.','May help ISPs and suppliers maintain existing router supply without abrupt disruption.','Limited waivers; hardware changes outside scope remain prohibited.',12,1,110);
INSERT INTO "regulatory_events" VALUES(12,'2026-06-12','conditional_approval','Miri and Arcadyan router Conditional Approvals','Miri/Arcadyan approvals','FCC reflected Conditional Approvals for the Miri X10 Travel router and specified Arcadyan routers for T-Mobile, AT&T, and Verizon devices.','Specified models/families were exempted for a limited period.','Conditional approvals are time-limited and scope-specific.',10,1,120);
INSERT INTO "regulatory_events" VALUES(13,'2026-06-26','hardware_waiver','Verizon and Arcadyan limited hardware-change waivers','Verizon/Arcadyan waivers','OET granted limited hardware-change waivers for Verizon and Arcadyan.','May help avoid broadband equipment supply disruption for existing authorized covered routers.','Limited waivers; not a blanket exception.',14,1,130);
INSERT INTO "regulatory_events" VALUES(14,'2026-07-01','proposed_rulemaking','FCC proposes component-related equipment authorization changes and permanent update-waiver codification','Proposed component rules','FCC released an item proposing broader component-related prohibitions and proposing to codify/make permanent certain software/firmware waivers.','Consumers and watchdogs should track this because the rules could change how covered components and updates are treated.','Proposed; not final in this data set.',16,1,140);
INSERT INTO "regulatory_events" VALUES(15,'2026-07-07','covered_list_snapshot','Covered List updated July 7, 2026','Latest included Covered List','FCC Appendix A as updated July 7, 2026 continues to list routers produced in a foreign country, except routers granted Conditional Approval by DoW or DHS.','Confirms the router entry remains on the latest Covered List snapshot included in this database.','Use the live FCC Covered List page for future updates.',17,1,150);
PRAGMA writable_schema=ON;
INSERT INTO sqlite_master(type,name,tbl_name,rootpage,sql)VALUES('table','search_index','search_index',0,'CREATE VIRTUAL TABLE search_index USING fts5(
            table_name UNINDEXED,
            row_id UNINDEXED,
            title,
            body,
            source_url UNINDEXED
        )');
INSERT INTO "search_index" VALUES('sources',1,'FCC Updates Covered List to Include Foreign-Made Consumer Routers, Prohibiting Approval of New Models','FCC fact sheet explaining the Covered List update for foreign-produced consumer routers, impact on new authorizations, continued use of existing routers, and Conditional Approval route.','https://docs.fcc.gov/public/attachments/DOC-420034A1.pdf');
INSERT INTO "search_index" VALUES('sources',2,'FCC''s Public Safety and Homeland Security Bureau Announces Addition of Routers Produced in Foreign Countries to FCC Covered List','Public Notice adding routers produced in a foreign country to the Covered List except routers granted Conditional Approval by DoW or DHS.','https://docs.fcc.gov/public/attachments/DA-26-278A1.pdf');
INSERT INTO "search_index" VALUES('sources',3,'OET Announces Waiver of Prohibitions on Certain Class I Permissive Changes to Covered Routers','Initial router waiver allowing certain software and firmware updates for already-authorized covered routers through March 1, 2027; later extended and expanded by DA 26-454.','https://docs.fcc.gov/public/attachments/DA-26-286A1.pdf');
INSERT INTO "search_index" VALUES('sources',4,'OET Announces Extension and Expansion of Waiver for Certain Software and Firmware Permissive Changes to Covered UAS, UAS Critical Components, and Routers','Extends and expands software/firmware update waivers through at least January 1, 2029 for covered routers authorized before March 23, 2026.','https://docs.fcc.gov/public/attachments/DA-26-454A1.pdf');
INSERT INTO "search_index" VALUES('sources',5,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','First router Conditional Approvals, including specified Netgear and Adtran router classes.','https://docs.fcc.gov/public/attachments/DA-26-351A1.txt');
INSERT INTO "search_index" VALUES('sources',6,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds eero/Amazon Leo router Conditional Approvals, with dates reflected in the FCC appendix.','https://docs.fcc.gov/public/attachments/DA-26-390A1.txt');
INSERT INTO "search_index" VALUES('sources',7,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Calix and Alpha Networks router Conditional Approvals to the Covered List appendix.','https://docs.fcc.gov/public/attachments/DA-26-542A1.pdf');
INSERT INTO "search_index" VALUES('sources',8,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Sagemcom USA FAST router Conditional Approvals.','https://docs.fcc.gov/public/attachments/DA-26-548A1.pdf');
INSERT INTO "search_index" VALUES('sources',9,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Miri Technologies Miri X10 Travel router Conditional Approval.','https://docs.fcc.gov/public/attachments/DA-26-584A1.pdf');
INSERT INTO "search_index" VALUES('sources',10,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Arcadyan router Conditional Approvals covering specified T-Mobile 5G FWA, AT&T BGW 720, and Verizon devices.','https://docs.fcc.gov/public/attachments/DA-26-585A1.pdf');
INSERT INTO "search_index" VALUES('sources',11,'AT&T Services Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants AT&T a limited waiver for targeted Class I and Class II hardware permissive changes to covered routers for one year.','https://docs.fcc.gov/public/attachments/DA-26-491A1.pdf');
INSERT INTO "search_index" VALUES('sources',12,'NCTA Petition for Expedited Waiver to Permit Targeted Hardware Changes to Covered Routers','Grants NCTA member suppliers a limited waiver for specified hardware substitutions in existing authorized covered routers.','https://docs.fcc.gov/public/attachments/DA-26-571A1.pdf');
INSERT INTO "search_index" VALUES('sources',13,'Sercomm Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Sercomm a limited waiver for end-of-life component changes in existing authorized covered routers.','https://docs.fcc.gov/public/attachments/DA-26-572A1.pdf');
INSERT INTO "search_index" VALUES('sources',14,'Verizon Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Verizon a limited waiver for memory-related, substrate, and end-of-life component changes for covered routers for one year.','https://docs.fcc.gov/public/attachments/DA-26-641A1.pdf');
INSERT INTO "search_index" VALUES('sources',15,'Arcadyan Technology Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Arcadyan a limited waiver for targeted Class I and Class II permissive hardware changes to consumer-grade routers with existing equipment authorizations.','https://docs.fcc.gov/public/attachments/DA-26-642A1.pdf');
INSERT INTO "search_index" VALUES('sources',16,'Protecting Against National Security Threats to the Communications Supply Chain Through the Equipment Authorization Program - Further Notice','July 2026 item proposing broader component-related rules and proposing to codify/make permanent certain software and firmware waivers.','https://docs.fcc.gov/public/attachments/DOC-422746A1.pdf');
INSERT INTO "search_index" VALUES('sources',17,'Covered List Updated July 7, 2026','Appendix A lists the Covered List as updated July 7, 2026 and includes the router entry dated March 23, 2026.','https://docs.fcc.gov/public/attachments/DA-26-673A1.pdf');
INSERT INTO "search_index" VALUES('sources',18,'FCC Covered List and Conditional Approvals Web Page','FCC public page where the current Covered List and router Conditional Approvals are published.','https://www.fcc.gov/supplychain/coveredlist');
INSERT INTO "search_index" VALUES('regulatory_events',1,'Foreign-produced routers added to FCC Covered List','The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS. New covered router models generally cannot enter the U.S. market through new FCC equipment authorization unless conditionally approved.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',2,'FCC explains impact on consumers and retailers','The FCC fact sheet says existing authorized router models and previously purchased routers are not prohibited by the update. Consumers may continue to use already-purchased routers; retailers may continue selling previously authorized models.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',3,'Initial software/firmware update waiver for covered routers','OET announced a waiver allowing certain Class I permissive software and firmware changes for already-authorized covered routers. Reduced risk that already-deployed routers would stop receiving security-related updates immediately after the Covered List update.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',4,'Netgear and Adtran router Conditional Approvals','FCC reflected DoW Conditional Approvals for specified Netgear and Adtran router product families. Certain specified foreign-produced router families were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',5,'eero router Conditional Approvals','FCC reflected Conditional Approvals for eero/Amazon Leo router families. Specified eero/Amazon Leo routers were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',6,'Software/firmware waiver extended and expanded through at least January 1, 2029','OET extended the software/firmware update waiver to at least January 1, 2029 and expanded it to analogous Class II permissive changes. Already-authorized covered routers may continue to receive functionality, compatibility, and security updates that mitigate harm.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',7,'AT&T limited hardware-change waiver','OET granted AT&T a limited waiver for targeted hardware changes to existing authorized covered routers. Helps avoid supply disruptions for affected broadband equipment.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',8,'Nokia router Conditional Approvals','FCC reflected Conditional Approvals for specified Nokia router products. Specified Nokia router products were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',9,'Calix and Alpha Networks router Conditional Approvals','FCC reflected Conditional Approvals for specified Calix and Alpha Networks router products. Specified Calix and Alpha Networks routers were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',10,'Sagemcom FAST router Conditional Approvals','FCC reflected Conditional Approvals for Sagemcom USA FAST3994, FAST3897, FAST5698, FAST5699, and FAST5999 routers. Specified Sagemcom routers were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',11,'NCTA and Sercomm limited hardware-change waivers','OET granted limited waivers involving specified hardware substitutions or end-of-life component changes. May help ISPs and suppliers maintain existing router supply without abrupt disruption.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',12,'Miri and Arcadyan router Conditional Approvals','FCC reflected Conditional Approvals for the Miri X10 Travel router and specified Arcadyan routers for T-Mobile, AT&T, and Verizon devices. Specified models/families were exempted for a limited period.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',13,'Verizon and Arcadyan limited hardware-change waivers','OET granted limited hardware-change waivers for Verizon and Arcadyan. May help avoid broadband equipment supply disruption for existing authorized covered routers.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',14,'FCC proposes component-related equipment authorization changes and permanent update-waiver codification','FCC released an item proposing broader component-related prohibitions and proposing to codify/make permanent certain software/firmware waivers. Consumers and watchdogs should track this because the rules could change how covered components and updates are treated.',NULL);
INSERT INTO "search_index" VALUES('regulatory_events',15,'Covered List updated July 7, 2026','FCC Appendix A as updated July 7, 2026 continues to list routers produced in a foreign country, except routers granted Conditional Approval by DoW or DHS. Confirms the router entry remains on the latest Covered List snapshot included in this database.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',1,'Are all foreign-made routers now illegal to own?','No. The FCC said the March 23, 2026 update does not affect previously purchased consumer-grade routers. The rule change targets new covered router models and FCC equipment authorization. Consumers can continue to use routers they already lawfully purchased or acquired. Retailers can also continue to sell, import, or market router models that were previously approved through FCC equipment authorization.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',2,'Can I still buy a router that was made outside the United States?','Yes, if it is an existing model previously authorized by the FCC or a model with a valid Conditional Approval. The consumer-friendly rule of thumb is: previously authorized existing models are not banned by this update, while new foreign-produced covered router models generally need a Conditional Approval route before they can be authorized, imported, marketed, or sold.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',3,'Should I keep installing router firmware updates?','Yes. Use legitimate updates from the router maker or your ISP. The FCC/OET extended and expanded a waiver so already-authorized covered routers may continue receiving software and firmware updates that mitigate harm through at least January 1, 2029. This includes updates that maintain functionality, patch vulnerabilities, or support compatibility.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',4,'What is a Conditional Approval?','It is a time-limited exemption for specific devices or device families. A Conditional Approval means DoW or DHS determined that the specified router device or class of devices does not pose unacceptable risks for the stated scope and dates. It is not necessarily a permanent clearance for all products made by that company.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',5,'What if my router came from my internet provider?','You can keep using it, but check for notices from the provider about replacement or firmware updates. ISP-supplied routers may be affected by the same Covered List framework, but some providers and suppliers have received limited hardware waivers or Conditional Approvals. Consumers should not unplug or discard working equipment solely because it was manufactured abroad.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',6,'Does Conditional Approval mean a router is guaranteed secure?','No. It is a national-security Covered List determination, not a consumer security guarantee. Consumers should still use normal router safety practices: install updates, use strong Wi-Fi passwords, disable unnecessary remote administration, and replace end-of-life products that no longer receive updates.',NULL);
INSERT INTO "search_index" VALUES('consumer_faqs',7,'How often should this site update its router data?','At least weekly, and immediately after FCC Covered List updates. The FCC maintains a live Covered List and Conditional Approvals page. This database has a current-as-of date and should be refreshed before publication of any compliance-sensitive claims.',NULL);
INSERT INTO "search_index" VALUES('content_pages',1,'What the FCC router action means for consumers','A plain-English landing page for consumers and router buyers. # What changed

The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS.

# What did not change

You can continue using a router you already lawfully purchased or acquired. Previously authorized existing router models are not prohibited by the March 23 update.

# What to do now

Keep installing legitimate software and firmware updates. Check whether your router maker or internet provider still supports your model. For new purchases, prefer sellers that can identify FCC authorization status or a valid Conditional Approval when relevant.',NULL);
INSERT INTO "search_index" VALUES('content_pages',2,'Router buying guide after the FCC Covered List update','Guidance for consumers considering a new router purchase. # Buying checklist

1. Confirm the product is an existing FCC-authorized model or is covered by a valid Conditional Approval.
2. Check the manufacturer''s support page for firmware update history.
3. Avoid unsupported/end-of-life models even if they are legal to use.
4. Keep receipts and model numbers; approvals and support status are model-specific.

# Important caveat

This database is educational. It does not replace checking the live FCC Covered List or the FCC Equipment Authorization database for a specific product.',NULL);
INSERT INTO "search_index" VALUES('content_pages',3,'Current router Conditional Approvals in this dataset','Explains and lists active Conditional Approvals. # Conditional Approvals

Conditional Approval is a scoped, time-limited exemption. The same company may have approved and unapproved products, so product family and model details matter.

Use the `vw_active_conditional_approvals` view to render a current table and include approval end dates.',NULL);
INSERT INTO "search_index" VALUES('content_pages',4,'Firmware and software updates for existing routers','Explains why consumers should keep updating routers. # Updates are still important

OET extended and expanded a waiver through at least January 1, 2029 for software and firmware updates that mitigate harm for covered routers authorized before March 23, 2026.

That means your site should not tell consumers to avoid updates. Instead, guide them toward legitimate updates from manufacturers or ISPs.',NULL);
INSERT INTO "search_index" VALUES('content_pages',5,'Notes for retailers and marketplaces','Short guidance for product-page compliance language. # Retailer guidance

Avoid broad statements such as "all foreign-made routers are banned" or "all products from this brand are exempt."

Safer product-page language should distinguish:
- previously authorized existing models,
- new models,
- Conditional Approval scope,
- approval or waiver expiration dates,
- whether the claim is about sale/import/marketing, use, firmware updates, or hardware changes.',NULL);
CREATE TABLE 'search_index_config'(k PRIMARY KEY, v) WITHOUT ROWID;
INSERT INTO "search_index_config" VALUES('version',4);
CREATE TABLE 'search_index_content'(id INTEGER PRIMARY KEY, c0, c1, c2, c3, c4);
INSERT INTO "search_index_content" VALUES(1,'sources',1,'FCC Updates Covered List to Include Foreign-Made Consumer Routers, Prohibiting Approval of New Models','FCC fact sheet explaining the Covered List update for foreign-produced consumer routers, impact on new authorizations, continued use of existing routers, and Conditional Approval route.','https://docs.fcc.gov/public/attachments/DOC-420034A1.pdf');
INSERT INTO "search_index_content" VALUES(2,'sources',2,'FCC''s Public Safety and Homeland Security Bureau Announces Addition of Routers Produced in Foreign Countries to FCC Covered List','Public Notice adding routers produced in a foreign country to the Covered List except routers granted Conditional Approval by DoW or DHS.','https://docs.fcc.gov/public/attachments/DA-26-278A1.pdf');
INSERT INTO "search_index_content" VALUES(3,'sources',3,'OET Announces Waiver of Prohibitions on Certain Class I Permissive Changes to Covered Routers','Initial router waiver allowing certain software and firmware updates for already-authorized covered routers through March 1, 2027; later extended and expanded by DA 26-454.','https://docs.fcc.gov/public/attachments/DA-26-286A1.pdf');
INSERT INTO "search_index_content" VALUES(4,'sources',4,'OET Announces Extension and Expansion of Waiver for Certain Software and Firmware Permissive Changes to Covered UAS, UAS Critical Components, and Routers','Extends and expands software/firmware update waivers through at least January 1, 2029 for covered routers authorized before March 23, 2026.','https://docs.fcc.gov/public/attachments/DA-26-454A1.pdf');
INSERT INTO "search_index_content" VALUES(5,'sources',5,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','First router Conditional Approvals, including specified Netgear and Adtran router classes.','https://docs.fcc.gov/public/attachments/DA-26-351A1.txt');
INSERT INTO "search_index_content" VALUES(6,'sources',6,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds eero/Amazon Leo router Conditional Approvals, with dates reflected in the FCC appendix.','https://docs.fcc.gov/public/attachments/DA-26-390A1.txt');
INSERT INTO "search_index_content" VALUES(7,'sources',7,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Calix and Alpha Networks router Conditional Approvals to the Covered List appendix.','https://docs.fcc.gov/public/attachments/DA-26-542A1.pdf');
INSERT INTO "search_index_content" VALUES(8,'sources',8,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Sagemcom USA FAST router Conditional Approvals.','https://docs.fcc.gov/public/attachments/DA-26-548A1.pdf');
INSERT INTO "search_index_content" VALUES(9,'sources',9,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Miri Technologies Miri X10 Travel router Conditional Approval.','https://docs.fcc.gov/public/attachments/DA-26-584A1.pdf');
INSERT INTO "search_index_content" VALUES(10,'sources',10,'Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Adds Arcadyan router Conditional Approvals covering specified T-Mobile 5G FWA, AT&T BGW 720, and Verizon devices.','https://docs.fcc.gov/public/attachments/DA-26-585A1.pdf');
INSERT INTO "search_index_content" VALUES(11,'sources',11,'AT&T Services Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants AT&T a limited waiver for targeted Class I and Class II hardware permissive changes to covered routers for one year.','https://docs.fcc.gov/public/attachments/DA-26-491A1.pdf');
INSERT INTO "search_index_content" VALUES(12,'sources',12,'NCTA Petition for Expedited Waiver to Permit Targeted Hardware Changes to Covered Routers','Grants NCTA member suppliers a limited waiver for specified hardware substitutions in existing authorized covered routers.','https://docs.fcc.gov/public/attachments/DA-26-571A1.pdf');
INSERT INTO "search_index_content" VALUES(13,'sources',13,'Sercomm Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Sercomm a limited waiver for end-of-life component changes in existing authorized covered routers.','https://docs.fcc.gov/public/attachments/DA-26-572A1.pdf');
INSERT INTO "search_index_content" VALUES(14,'sources',14,'Verizon Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Verizon a limited waiver for memory-related, substrate, and end-of-life component changes for covered routers for one year.','https://docs.fcc.gov/public/attachments/DA-26-641A1.pdf');
INSERT INTO "search_index_content" VALUES(15,'sources',15,'Arcadyan Technology Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Grants Arcadyan a limited waiver for targeted Class I and Class II permissive hardware changes to consumer-grade routers with existing equipment authorizations.','https://docs.fcc.gov/public/attachments/DA-26-642A1.pdf');
INSERT INTO "search_index_content" VALUES(16,'sources',16,'Protecting Against National Security Threats to the Communications Supply Chain Through the Equipment Authorization Program - Further Notice','July 2026 item proposing broader component-related rules and proposing to codify/make permanent certain software and firmware waivers.','https://docs.fcc.gov/public/attachments/DOC-422746A1.pdf');
INSERT INTO "search_index_content" VALUES(17,'sources',17,'Covered List Updated July 7, 2026','Appendix A lists the Covered List as updated July 7, 2026 and includes the router entry dated March 23, 2026.','https://docs.fcc.gov/public/attachments/DA-26-673A1.pdf');
INSERT INTO "search_index_content" VALUES(18,'sources',18,'FCC Covered List and Conditional Approvals Web Page','FCC public page where the current Covered List and router Conditional Approvals are published.','https://www.fcc.gov/supplychain/coveredlist');
INSERT INTO "search_index_content" VALUES(19,'regulatory_events',1,'Foreign-produced routers added to FCC Covered List','The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS. New covered router models generally cannot enter the U.S. market through new FCC equipment authorization unless conditionally approved.',NULL);
INSERT INTO "search_index_content" VALUES(20,'regulatory_events',2,'FCC explains impact on consumers and retailers','The FCC fact sheet says existing authorized router models and previously purchased routers are not prohibited by the update. Consumers may continue to use already-purchased routers; retailers may continue selling previously authorized models.',NULL);
INSERT INTO "search_index_content" VALUES(21,'regulatory_events',3,'Initial software/firmware update waiver for covered routers','OET announced a waiver allowing certain Class I permissive software and firmware changes for already-authorized covered routers. Reduced risk that already-deployed routers would stop receiving security-related updates immediately after the Covered List update.',NULL);
INSERT INTO "search_index_content" VALUES(22,'regulatory_events',4,'Netgear and Adtran router Conditional Approvals','FCC reflected DoW Conditional Approvals for specified Netgear and Adtran router product families. Certain specified foreign-produced router families were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(23,'regulatory_events',5,'eero router Conditional Approvals','FCC reflected Conditional Approvals for eero/Amazon Leo router families. Specified eero/Amazon Leo routers were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(24,'regulatory_events',6,'Software/firmware waiver extended and expanded through at least January 1, 2029','OET extended the software/firmware update waiver to at least January 1, 2029 and expanded it to analogous Class II permissive changes. Already-authorized covered routers may continue to receive functionality, compatibility, and security updates that mitigate harm.',NULL);
INSERT INTO "search_index_content" VALUES(25,'regulatory_events',7,'AT&T limited hardware-change waiver','OET granted AT&T a limited waiver for targeted hardware changes to existing authorized covered routers. Helps avoid supply disruptions for affected broadband equipment.',NULL);
INSERT INTO "search_index_content" VALUES(26,'regulatory_events',8,'Nokia router Conditional Approvals','FCC reflected Conditional Approvals for specified Nokia router products. Specified Nokia router products were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(27,'regulatory_events',9,'Calix and Alpha Networks router Conditional Approvals','FCC reflected Conditional Approvals for specified Calix and Alpha Networks router products. Specified Calix and Alpha Networks routers were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(28,'regulatory_events',10,'Sagemcom FAST router Conditional Approvals','FCC reflected Conditional Approvals for Sagemcom USA FAST3994, FAST3897, FAST5698, FAST5699, and FAST5999 routers. Specified Sagemcom routers were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(29,'regulatory_events',11,'NCTA and Sercomm limited hardware-change waivers','OET granted limited waivers involving specified hardware substitutions or end-of-life component changes. May help ISPs and suppliers maintain existing router supply without abrupt disruption.',NULL);
INSERT INTO "search_index_content" VALUES(30,'regulatory_events',12,'Miri and Arcadyan router Conditional Approvals','FCC reflected Conditional Approvals for the Miri X10 Travel router and specified Arcadyan routers for T-Mobile, AT&T, and Verizon devices. Specified models/families were exempted for a limited period.',NULL);
INSERT INTO "search_index_content" VALUES(31,'regulatory_events',13,'Verizon and Arcadyan limited hardware-change waivers','OET granted limited hardware-change waivers for Verizon and Arcadyan. May help avoid broadband equipment supply disruption for existing authorized covered routers.',NULL);
INSERT INTO "search_index_content" VALUES(32,'regulatory_events',14,'FCC proposes component-related equipment authorization changes and permanent update-waiver codification','FCC released an item proposing broader component-related prohibitions and proposing to codify/make permanent certain software/firmware waivers. Consumers and watchdogs should track this because the rules could change how covered components and updates are treated.',NULL);
INSERT INTO "search_index_content" VALUES(33,'regulatory_events',15,'Covered List updated July 7, 2026','FCC Appendix A as updated July 7, 2026 continues to list routers produced in a foreign country, except routers granted Conditional Approval by DoW or DHS. Confirms the router entry remains on the latest Covered List snapshot included in this database.',NULL);
INSERT INTO "search_index_content" VALUES(34,'consumer_faqs',1,'Are all foreign-made routers now illegal to own?','No. The FCC said the March 23, 2026 update does not affect previously purchased consumer-grade routers. The rule change targets new covered router models and FCC equipment authorization. Consumers can continue to use routers they already lawfully purchased or acquired. Retailers can also continue to sell, import, or market router models that were previously approved through FCC equipment authorization.',NULL);
INSERT INTO "search_index_content" VALUES(35,'consumer_faqs',2,'Can I still buy a router that was made outside the United States?','Yes, if it is an existing model previously authorized by the FCC or a model with a valid Conditional Approval. The consumer-friendly rule of thumb is: previously authorized existing models are not banned by this update, while new foreign-produced covered router models generally need a Conditional Approval route before they can be authorized, imported, marketed, or sold.',NULL);
INSERT INTO "search_index_content" VALUES(36,'consumer_faqs',3,'Should I keep installing router firmware updates?','Yes. Use legitimate updates from the router maker or your ISP. The FCC/OET extended and expanded a waiver so already-authorized covered routers may continue receiving software and firmware updates that mitigate harm through at least January 1, 2029. This includes updates that maintain functionality, patch vulnerabilities, or support compatibility.',NULL);
INSERT INTO "search_index_content" VALUES(37,'consumer_faqs',4,'What is a Conditional Approval?','It is a time-limited exemption for specific devices or device families. A Conditional Approval means DoW or DHS determined that the specified router device or class of devices does not pose unacceptable risks for the stated scope and dates. It is not necessarily a permanent clearance for all products made by that company.',NULL);
INSERT INTO "search_index_content" VALUES(38,'consumer_faqs',5,'What if my router came from my internet provider?','You can keep using it, but check for notices from the provider about replacement or firmware updates. ISP-supplied routers may be affected by the same Covered List framework, but some providers and suppliers have received limited hardware waivers or Conditional Approvals. Consumers should not unplug or discard working equipment solely because it was manufactured abroad.',NULL);
INSERT INTO "search_index_content" VALUES(39,'consumer_faqs',6,'Does Conditional Approval mean a router is guaranteed secure?','No. It is a national-security Covered List determination, not a consumer security guarantee. Consumers should still use normal router safety practices: install updates, use strong Wi-Fi passwords, disable unnecessary remote administration, and replace end-of-life products that no longer receive updates.',NULL);
INSERT INTO "search_index_content" VALUES(40,'consumer_faqs',7,'How often should this site update its router data?','At least weekly, and immediately after FCC Covered List updates. The FCC maintains a live Covered List and Conditional Approvals page. This database has a current-as-of date and should be refreshed before publication of any compliance-sensitive claims.',NULL);
INSERT INTO "search_index_content" VALUES(41,'content_pages',1,'What the FCC router action means for consumers','A plain-English landing page for consumers and router buyers. # What changed

The FCC added routers produced in a foreign country to the Covered List, except routers granted Conditional Approval by DoW or DHS.

# What did not change

You can continue using a router you already lawfully purchased or acquired. Previously authorized existing router models are not prohibited by the March 23 update.

# What to do now

Keep installing legitimate software and firmware updates. Check whether your router maker or internet provider still supports your model. For new purchases, prefer sellers that can identify FCC authorization status or a valid Conditional Approval when relevant.',NULL);
INSERT INTO "search_index_content" VALUES(42,'content_pages',2,'Router buying guide after the FCC Covered List update','Guidance for consumers considering a new router purchase. # Buying checklist

1. Confirm the product is an existing FCC-authorized model or is covered by a valid Conditional Approval.
2. Check the manufacturer''s support page for firmware update history.
3. Avoid unsupported/end-of-life models even if they are legal to use.
4. Keep receipts and model numbers; approvals and support status are model-specific.

# Important caveat

This database is educational. It does not replace checking the live FCC Covered List or the FCC Equipment Authorization database for a specific product.',NULL);
INSERT INTO "search_index_content" VALUES(43,'content_pages',3,'Current router Conditional Approvals in this dataset','Explains and lists active Conditional Approvals. # Conditional Approvals

Conditional Approval is a scoped, time-limited exemption. The same company may have approved and unapproved products, so product family and model details matter.

Use the `vw_active_conditional_approvals` view to render a current table and include approval end dates.',NULL);
INSERT INTO "search_index_content" VALUES(44,'content_pages',4,'Firmware and software updates for existing routers','Explains why consumers should keep updating routers. # Updates are still important

OET extended and expanded a waiver through at least January 1, 2029 for software and firmware updates that mitigate harm for covered routers authorized before March 23, 2026.

That means your site should not tell consumers to avoid updates. Instead, guide them toward legitimate updates from manufacturers or ISPs.',NULL);
INSERT INTO "search_index_content" VALUES(45,'content_pages',5,'Notes for retailers and marketplaces','Short guidance for product-page compliance language. # Retailer guidance

Avoid broad statements such as "all foreign-made routers are banned" or "all products from this brand are exempt."

Safer product-page language should distinguish:
- previously authorized existing models,
- new models,
- Conditional Approval scope,
- approval or waiver expiration dates,
- whether the claim is about sale/import/marketing, use, firmware updates, or hardware changes.',NULL);
CREATE TABLE 'search_index_data'(id INTEGER PRIMARY KEY, block BLOB);
INSERT INTO "search_index_data" VALUES(1,X'2D000083408B5300');
INSERT INTO "search_index_data" VALUES(10,X'000000000101030001010103');
INSERT INTO "search_index_data" VALUES(137438953473,X'00000F2E0230310306010312010601030D140C01020C01030D0C06010328060601030C02060103170101322A0601031E020330323604060103160C06010303010E01020701030C0B100C01020701030901060103090A060103280401370306010313040139040601030E140C01020D01030E0C06010329080601031802013304060103150D060103141106010308070601033F0306010327020136030601031A0101332A060103290101342A0601033702023534030601031B010235670A0601030B010137110C01020601030B100C010206010308020232300A06010310010161020601030809060103050106010306010601030401060103040106010304020601030302060103080206010304010601031801060103140206010306010601031201060103170106010316020601031E03080103040E021001020601030F0520010601031301100102040103040C22020E01020601030509010801030F0D010C010302141A3A010A0103061643010801030D2001060103110204626F7574260601030E07060103360304726F6164260601033904037570741D0601031A020763717569726564220601032A0706010333030474696F6E2906010206050276652B0801030522020464646564130C01020501030416060103100403696E670206010304050474696F6E020601020B04017306060103020106010302010601030201060103020106010302030C6D696E697374726174696F6E270601032203047472616E050601030A110C01020401030B02056666656374220601030D0702656419060103170D06010318030374657215060103211306010307020601020502066761696E7374100601020302026C6C2206010203030601033208080103100904056F77696E670306010305120601030603037068610706010305140E01020401030A0903057265616479030601030C110601031A01080103100903060103180A060103260206010316050601032F0302736F220601032D02056D617A6F6E060601030411080103080802016E2006010304030601030607060103110307616C6F676F75731806010313030164010601031801060102060108010308100110010205090C010303010E01020704010309010801020704010E01020704010304010801020704010801020704010E01020704010311010601030C030601030B010601030B010801030A0A010601030D010C01020501030A020C01020701030B010601030C010C01020301030A020E01020601030F15030E01020301030909010601030D010C010203010313010E01020301030C0B010C01020301030A011001020901030B0D0F020601031B02080103110F010601032801060103220106010323010A010305100E010801030942010801033A06010C010303170812010E01020301030F0E010601020503076E6F756E6365641506010303090173020601020A01060102030106010203030179280601032602077070656E646978060601030F010601030E0A0601030210060103030405726F76616C010C01020D01031A01060103130306010203010601020301060102030106010203010C01020301030A010601020309060103130E0601031702080103151F020C0102060103100206010204020801031F4A010601031D010801030B27020801032B0409017305060103050106010308010601030901060103080206010306080C01020701030D040C010207010306010C010205010305030C010205010305010C010208010305010C010206010305020C010207010305080601032B0206010315020601033D0110010205010307042007026564130601032A0F06010339090601031702077263616479616E0A06010303050C0102020103030F0C01020401030E010C01020401030B030165120601030E020601030F0C06010325020601020201060103210606010339010801033310020601030A01080103140A02017311060103081006010305070601031C050601030F020174040601030A060601030D010C0102020103030D0C01020901030A010C0102020103040506010313060601032504060103020406010314020C7574686F72697A6174696F6E100601020F03060103270D06010207020801031E21070601036101060103580E017301060103120E0601031809026564030601030D0106010312080601030F010601030F07080103081C01060103110306010319010601030F0606010315040A01030A161C010601031705060103350106010314020601032401060103250204766F69641906010313060601030E0B0601032A0206010332010601030B010662616E6E656423060103230A0601031502016523060103370306010317020601032103056361757365200601031B06060103350304666F726504060103131F0601033405060103230406010325020267770A0601030F020472616E642D0601031B03036F61642D0601030C060462616E641906010318060601030F060265721006010306100601030702057572656175020601020903017426080103071A03017923060102050403657273290601030B0403696E672A0C01020301030A02017902060103140106010318100601031401060103120D06010318020801030B1B0206010335010601031903080103201E0106010319010563616C69780706010303140E0102020103080903026D65260601020603016E22080103200E010C010202010336030601030303080103293704036E6F74130601031D0304766561742A06010345020665727461696E030C010208010306010601020A01060102050106010205010601020501060102050106010205010601020506060103100506010307010601030F0A0601031102046861696E100601020B04036E676519060102060406010207020C010207010306010601031F02060103150706010327070164290601030D070173030601020C010601020F070C01020C010311010601020B010C01020B01030C010C01020A010310010C01020C010310060601030E0306010317010601030C040601030F03060102080D0601033F030365636B2606010308030601034C010601031F0603696E672A0601034E06046C6973742A0601030B02046C61696D2D060103340601732806010329040273730306010209080801030A05040801030905060601030803060103140D0601031C06026573050601030C0307656172616E63652506010330020B6F64696669636174696F6E200601020D060179100601030D100601030E030C6D6D756E69636174696F6E731006010209040470616E79250601033706060103140608746962696C69747918060103210C0601033405066C69616E63652806010327050601030705056F6E656E740D0601030B010601030F02060103070D0601030E030C0102040103080A017304060102151C0601032203096E646974696F6E616C01060103190106010312030C010202010304010C010202010307010C010202010308010C010202010307010C010202010309010C010202010305080C01020601030C0106010312030C010206010305010C010204010304030C010204010304010C010207010304010C010205010304020C010206010304030601031602080103141F020C01020501030F010601032A01060102030106010314010801031E4A010601031C011201020401030604041E020601032A0C026C79130601032904046669726D2A0601030D080173210601031C04087369646572696E672A060103050504756D6572010C01020A01030D0E0601031213060103100106010317040601030D090173140C0102060103150C06010315020601031F040601032C0106010310020C010209010308010601030402080103042E040574696E756514080103170A040601031D0A080103210F020601031B050601032A0901640106010313090173210601030A030972706F726174696F6E0D0601020302060102040303756C64200601031E04066E74726965730206010211070179020601030A110601030A0E06010312080601031603057665726564010C010204010307010C01021401030D010C01020E01030E010C010211010310010601020D010601020D010C01020D01030C010601020D010601020D010601020D010C01020E010313010C01020D010310010C01020D010310010C01020C010312010601020E020C010202010306010C010203010308010E01020801030D0E020E01020801031213030601031A010601031006060103160106010321010C0102020103240106010318010601032B0106010318020601031C010601030801080103090A0106010319010E0102080103183C02060103220603696E670A0601030702077269746963616C04060102140206757272656E741206010307160601031B030C01020201032C01026461030601031903027461280601020A050462617365210601032A070601031802080103471405037365742B06010208040165280601031E0501641106010312050173060601030A1F0601032906060103320206010331020765706C6F796564150601031803057461696C732B06010320040A65726D696E6174696F6E270601030A090265642506010315030476696365250801030C100701730A060103131406010317070801030A1602026873020601031711060103170E0601031B0406010314040601032302026964290601032503057361626C65270601031F0404636172642606010331040772757074696F6E1D0601031B02060103120B01731906010315040874696E67756973682D0601032302016F290601034303026573220601030B030601031F0206010202030601034B0301770206010315110601031503060103040B0601031904060103120406010321010B656475636174696F6E616C2A06010349020365726F0606010303110E0102020103070802026E640D06010308010601030C0F0601030B0A06010325030601032C01060103310305676C69736829060103040303746572130601031E040272791106010311100601031F0208717569706D656E740F06010317010601020E0306010326060601031906060103100106010206020801031D2104060103330406010357020376656E2A0601033002057863657074020601030F110601030F0E06010313080601031B0304656D70742D0601031D0702656416060103160106010312030601031001060103150106010314020601031C0703696F6E050601020A010601020A010601020A010601020A010601020A010601020A1B0601030706060103110306697374696E6701060103160B0601030E010601030E02060103160506010307050601030E0406010316020601031404080103071A06060103360106010312020601020701060103260424082A081A1C08080809091309811B100B0A130B0A130A0B1C13130C0E140D1411132B0912120E817E0E12081D696D13263217392D0D521F1212111A090B0A100E0C09080A0D3715091C0A0B470B260850140A0B0B0824090E120D13101412230D813F090B080F2232220808150A0D17815D0A0E1A0909160A0808170E0C11090C131D090C0B13080F0818211213220C0A0E380A1B0B222D');
INSERT INTO "search_index_data" VALUES(137438953474,X'00000F1D0930657870616E6465640306010317150C0102070103100C0601031208060103100701730406010304060473696F6E040601020604066564697465640B060102070106010205010601020601060102050106010207040769726174696F6E2D0601033004076C61696E696E670106010305080173140601020317060103020106010302030674656E6465640306010315150C0102050103030C06010310080601030E0701730406010302060473696F6E04060102040104666163740106010303130601030403066D696C696573160801030E08010601030B070601031A070601030D0601792B0601031D03027374080601030514060102030504333839371C0601030A06033939341C060103090504353639381C0601030B0801391C0601030C06033939391C0601030E02026363010C010202010302010801020213030601020C010C01020C01030E010601020C010601020C010601020C010601020C080C010202010302010E01020701030324010C010202010303020601030201060103020306010302010601030201060103020206010302020C0102020103020106010302010A0103041A21010601030D010601030E040801030807010E01020401030F5301100102070103134007020169270601031D0306726D776172650306010309010C01020D0103060C06010313050C01020401030D030C0102030103060806010313040C01020701031F0206010311030601034A0106010326020C01020201031C010601033B04027374050601030202026F72010601030A020601030B010C01020901030F0710010206050103080F010C010204010309010E010205050103070112010204050103070C05010E01020605010307060C01020701030F01080103071201080103060F02080103090F01080103060D010801030612010801030611020A0103060C0F01080103080D060A0103081E0F0106010309030E01020801030753010A0103032437020E0102060103190A010C01020301030404046569676E010C01020801030B010C010210010309110C01020201030903060103110B060103110106010204010601032906060103150406010311020872616D65776F726B260601031E030669656E646C79230601031803026F6D050601020B010601020B010601020B010601020B010601020B010601020B1A06010306020C01020701030B060601033A0106010319020C756E6374696F6E616C69747918060103200C0601032F030572746865721006010211020277610A0601030C010967656E6572616C6C79130601031C100601032E0204726164650F06010313130601031104046E746564020601031111060103110606010303040601030302060103030206010315080601031D0601730B0601030201060103020106010302010601030201060103020208756172616E746565270601030F0A0164270601020903066964616E63652A060103020308010303090501652A060102040206010335010868617264776172650B0C01020B01030F010C01020A01030B010601020A0106010209010C01020B01030F0A0C01020501030B040C010206010308020C0102060103050706010327070601033E04016D18060103270C060103230806010320030173280601031903027665260601032405060103160203656C701D06010311020601030D050173190601031202066973746F72792A0601032802076F6D656C616E64020601020703017720060103200806010202010169030601020A080601030B040601030A06060103090E060102030106010203020764656E74696679290601035F0201662306010303030601020304060103310201690B0601030E040601030D090601031502066C6C6567616C2206010208020A6D6D6564696174656C7915060103201306010306030470616374010601030F130601020404036F727422060103310B060103380703616E742A06010344020601030C07026564230601033902016E020C01020F010307040601030C060601030D010601030D06060103070E0801030F1B080601031302060102060305636C75646501060102072A0601032F0801642106010327080173110601030E130601032B0703696E6705060103060305697469616C0306010302120601020203057374616C6C27060103180803696E672406010205050601034605036561642C0601033403067465726E6574260601020903060103520307766F6C76696E671D06010306020173230801030519020E0102030103032A020C010208010304030A0103100933010601030C0206010335030170240601030C02060103130401731D060103120F0601033D02017418060103110B0601030402080103022A0108010306320106010303030601034A0302656D10060103041006010305030173280601020801076A616E75617279040601030C140C01020B01030C0C0601032708060103160203756C791006010302010C01020501030A100C01020501030701046B6565702406010204020601030403060103450106010338020601030601076C616E64696E672906010305040567756167652D080103081B0303746572030601031405027374210601032303067766756C6C7922060103270706010330020465617374040601030B140C01020A01030B0C0601032604060103030406010315030367616C2A0601033404076974696D61746524060103040506010347030601033803016F060601030511080103090802036966650D0601030A010601030E0F0601030D0A06010327030601032E03056D697465640B06010306010601030701060103050106010305010601030507060103190106010315020C010204010307010601031301060103180106010317010C010205010304010601031F010C01020501030406060103060106010326050601031003027374010C010205010308010C01021501030E030601020E010601020E010C01020E01030D010601020E010601020E010601020E070C010203010307010C010204010309010C01020901030E02060103240C0E01020301030C1B050601031D0106010309010801030A0A010601031A010C01020901035305017311060103041A06010304030276652806010310020601035002056F6E676572270601032B01046D61646501060102092106010205010601020A020601033408060103120306696E7461696E1D06010315070601032E090173280601030E03026B65100601030E100601030F05017224060103090506010350030A6E75666163747572656426060103380C01722A060103210D01732C0601033B0303726368030601031101060103140D060103131106010307070601033E030601032604036B657413060103220F0601033307026564230601033A0703696E672D060103390706706C616365732D060102060304747465722B0601032103017914080103160A040601031C0506010310020601030C050601031A02060103160506010315020365616E270601020505017325060103110406010207030601032A03046D6265720C0601030404036F72790E060103080203697269090801030304150C010202010308030674696761746518060103260C06010322080601031F02056F62696C650A0601030A1406010312030364656C23080103080A0606010357010A0103152809010601031F0601730106010210120601031B010801030A1B0A06010319040801031A1D01080103200F0606010338010601032F03080103270402017926080102040601086E6174696F6E616C1006010204170601030602036374610C0C0102020103031106010202020A65636573736172696C79250601032D03026564230601032F030574676561720506010308110C0102020103090405776F726B730706010306140E01020501030B09030177010C01020F01031112080103180E0F06010317010601032806060103590106010307030601032802016F220601030205080103022A03036B69611A0E010202010308060304726D616C270601031403017414060103100E0601030C010601032202080103200E010601032E010601030B020801032616010601034C020601032E040265732D06010202040369636502060103030E06010212070173260601030A030177220601020707060103440206756D626572732A0601033C01036F65740306010202010601020211060103020306010302010601030204060103020206010302050601030F080601030D020166010C01020E010315010601020C010601020501060102070106010204010601020401060102040106010204010601020401060102040306010309010601030D0F0601030C060601031A020601031D0206010326010801031D0A020601032D030374656E280601020302016E0106010310020601020711060102050D060103210301650B060103160306010315020172020601031611060103160A0601030A040601031A01080103290B010801030E2F010801030A2A010A01030B0A0A010A0103101B09030C010322122114010801031640020601033C010A0103161A110206757473696465230601020B0202776E220601020A010470616765120C01020901030416060103160106010306010601032403080103061C03077373776F726473270601031E0303746368240601033002056572696F64160601031A0106010316030601031401060103190106010318020601032004066D616E656E74100601030F100C01020A010310050601032F0506697373697665030601020B010601020E0706010310040601030E060601030A03060103160601740C060102080306746974696F6E0B06010205010601020301060102040106010203010601020502046C61696E290601030302036F73652506010321020872616374696365732706010317030465666572290601035B040776696F75736C79140801030C170E0801030E2C0108010309160606010334040601032403066F6475636564010601030C010C01020E010306110C01020301030603060103120B0601030E020601032A0606010312070174160601030D140801030F50010601031C02080103051C0801731A0801030A06010601030D0A060103330206010328040601031A020601031804046772616D10060102100407686962697465641406010311150601033B0903696E67010601020C0A036F6E7303060102061D0601030A0405706F73657320060102030703696E67100801030508100801030608040774656374696E67100601020204057669646572260C01020A01030D03060103530901732606010321020575626C6963020C010204010302100601030307056174696F6E2806010324060473686564120601030F0421080B210E0E121F080B101D080E0B0A0B080A8121085309812B3C0F0D39180C091510291C0F08130D4E12080E0F080D0E0D210E12120D16100F0F092F11080D0A110C0F0A120E2B0D0D230E08201A1F0E0D0A0912220A180E1E65780D0E0C1F12080E0D110808230F090A0D0B270A120B0A1317111C34091412110914152A0E0E0B32090F080D0D32610A170D510D09230E0A251A2608210B0A0F0B253119220B130A0F0C110E1408140C');
INSERT INTO "search_index_data" VALUES(137438953475,X'00000C38093070757263686173652A06010309090164140801030D100E0801030F1B0706010331090173290601035A010872656365697074732A0601033906027665180601031F0F0601032C08016426060103250703696E67150601031C0F0601031C0305647563656415060103140307666C6563746564060601030B1006010303010601030303060103030106010303010601030302060103030406726573686564280601032203056C617465640E060103090206010308050601031E0B0C010205010309040565617365642006010303050476616E74290601036903056D61696E73210601032004036F7465270601032103046E6465722B0601032A0305706C6163652706010324030601034D08046D656E74260601030F03067461696C65722D06010309090173140C01020801031D0E0601032B0B06010204020369736B1506010315050173250601032302046F757465010601031B2206010333060172030601030302080103030A010601030601060103070106010306010601030801060103040706010310010601030B010601031A0106010309020E01020501030C09010C01020301030A030E01020301030906010C01020601030C01060102040106010317010C01020501030B030601031E01080103191D010C01020701032C010C01020601030801060103190106010205010C0102070103150106010209011201020501030A250C1A010C0102020103080106010203070173010E01020B01030E0B010E01020D0103050D010C01020F01030F010C010217010311010601020601060102060106010206010601020601060102060106010206010C01020F010314010C01020E010311010C01020E010311010C01020D010313010C01020F010314040E0102040103050D010801030E10010E010209010313080206010310010601031B01060103110206010313010801030F05020601030F0106010317020801030D09010E010206010312140206010319020601031503080103110D030E0102080103081D01060103130203756C65220601031401060103190501731006010309100601031D0101730206010203110601032117060103220204616665722D0601031E0502747902060102052506010316030667656D636F6D0806010303140E0102020103070C03026964220601030503026C652D0601033703026D65260601031B05060103130302797314060103060204636F70652506010327080601032C0601642B0601030E02056563757265270601020A060369747902060102080E06010205050601031D03060103230F080103070903026C6C22060103300503657273290601035C0503696E67140601032003076E7369746976652806010328030572636F6D6D0D0C0102020103031006010204040576696365730B060102040204686565740106010304130601030503036F72742D060103020403756C6420060103180406010202020601032D0106010311010C01020401032004080103052A010601032202036974652806010206040601032C02076E617073686F74210601032602016F2406010315070601031B03066674776172650306010307010C01020B0103050C06010311050C01020301030B030C0102020103050806010312040601031D0506010348030C01020401031A03026C64230601033C0403656C79260601033403026D652606010320020770656369666963250601030905080103431B0802656405060103070506010308020601030A0A080103080A010601030C03080103070601080103070901060103100106010307010801030D0D070601031802057461746564250601032606056D656E74732D0601030D060173230601020E05027573290601036201060103400303696C6C230601020404060103120206010354030601030B03026F70150601031B0304726F6E67270601031B020C7562737469747574696F6E730C0601030C11060103090604726174650E0601030A030263682D0601030E030670706C6965642606010314080272730C0601030511060103140906010323060179100601020A09060103140406010318020601031105036F7274240601033306080103231E08017329060103550101740A0801030907010C0102030103040E0C010203010305050801031105020461626C652B0601032D03067267657465640B0C01020A010309010601020901060102090106010208010C01020A0103080A0601030A0701732206010316020B6563686E6F6C6F6769657309060103040A01790F0601020303026C6C2C0601032F0203686174150601031603060103250A06010336010601020801080103210E0108010316220206010329020601035D030801031E0D0301650106010306010601030C040601030D010601030B09080102080701080103050C0106010306010A0103020C15010801030213010601032203060103040606010307020601031C010801031D07010A010303050F010E01020C01030C0C010801030708010801031710010801030C10020601030C011001020301030E0C27011201020601030E143108010801031213020601033304016D2C0601033604017922060103250106010335070601033203026973200601031A01060103290206010325010601032A040C01020501031702060103460106010207020601031A03057265617473100601020604046F756768030601031001060103090C0601020C030601032305060102080A0601033A020601032408060103130303756D62230601031B0203696D652506010305060601030F02016F0106010206010C01021201030B010601020D0106010210030601030A040C01020D010312010801020707010601020C010601020B010C01020D010311010C01020701030C030C01020601030B0106010318040A0103090B0E010601030D070601030D010601030B010E0102090103220F07080103172D0106010335010601032901060103310304776172642C0601033702047261636B2006010319040376656C0906010307150601030A030565617465642006010326010175130601032002026173040801021203010601020801060102080106010208010601020801060102080106010208020B6E61636365707461626C65250601032204077070726F7665642B06010319030469746564230601020D03046C657373130601032803096E656365737361727927060103200304706C7567260601032F0309737570706F727465642A0601032B02057064617465010601030903060103071006010314010C0102050103250306010307080601020B020601030A010601032605060102070106010340010C01020A010327070164110C010204010309100C0102040103060701730106010203020601030A120601031F0306010324080601032404100102080103051D0E0206010312010801031916010601030B010601034B0312010205010309161808010601033C0603696E672C060103070202736108060103041406010308030165010601031413060103190E06010323020601030303080103130903060103360106010322020601033A0303696E672606010305030601032B010576616C696423060103130606010365010601031B02066572697A6F6E0A06010312040C0102020103031006010316010C01020201030902036965772B06010328020E756C6E65726162696C697469657324060103310201772B060103240106776169766572030C0102040103040106010208070C010208010307010C010206010308010C010207010306010C010206010306010C010208010306060C010206010305030C010204010308010C010207010308070601020C04060103140806010312010601032F07017304060103080C060103140D0C010208010305020C01020801030701060103140606010328030173230601020903060103370307746368646F677320060103170202656212060102080304656B6C7928060103040302726516060103150106010311030601030F01060103140106010313020601031B0406010337020368617425060102020106010202031001020201030C1A1F0302656E2906010368040272651206010305040474686572290601034D04060103320303696C6523060103270301792C06010303020169270601031C0302746806060103090906010315140601031105036F75741D0601031902066F726B696E6726060103320303756C64150601031A0103783130090601030615060103090104796561720B0601031703060103160301732306010302010601030202026F752606010302030801032808040172240601030B050801034E0A030601032B040F14080F0E080F0C2C0D1E0C0B0C0A0B110B0D150A0810813981540F0D120B0E1609090E0910080C1F090A0A0E140C100A2C0F0E0D41090A09143F0C0C080E19090B180B090D131710081F0B2C0812080935811608122F0C2E0A0F81080B0B0F0C0828120E0B0B100B1044134B0A0E2C0F16220A150869270D0E090B27190909100A0808130A0D0A0F100D0F');
CREATE TABLE 'search_index_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
INSERT INTO "search_index_docsize" VALUES(1,X'00000F1A00');
INSERT INTO "search_index_docsize" VALUES(2,X'0000141600');
INSERT INTO "search_index_docsize" VALUES(3,X'00000E1A00');
INSERT INTO "search_index_docsize" VALUES(4,X'0000161500');
INSERT INTO "search_index_docsize" VALUES(5,X'00000D0B00');
INSERT INTO "search_index_docsize" VALUES(6,X'00000D0E00');
INSERT INTO "search_index_docsize" VALUES(7,X'00000D0D00');
INSERT INTO "search_index_docsize" VALUES(8,X'00000D0700');
INSERT INTO "search_index_docsize" VALUES(9,X'00000D0900');
INSERT INTO "search_index_docsize" VALUES(10,X'00000D1200');
INSERT INTO "search_index_docsize" VALUES(11,X'00000E1600');
INSERT INTO "search_index_docsize" VALUES(12,X'00000D1000');
INSERT INTO "search_index_docsize" VALUES(13,X'00000D1000');
INSERT INTO "search_index_docsize" VALUES(14,X'00000C1500');
INSERT INTO "search_index_docsize" VALUES(15,X'00000E1700');
INSERT INTO "search_index_docsize" VALUES(16,X'0000111300');
INSERT INTO "search_index_docsize" VALUES(17,X'0000061400');
INSERT INTO "search_index_docsize" VALUES(18,X'0000080E00');
INSERT INTO "search_index_docsize" VALUES(19,X'0000082900');
INSERT INTO "search_index_docsize" VALUES(20,X'0000072200');
INSERT INTO "search_index_docsize" VALUES(21,X'0000082400');
INSERT INTO "search_index_docsize" VALUES(22,X'0000061900');
INSERT INTO "search_index_docsize" VALUES(23,X'0000041500');
INSERT INTO "search_index_docsize" VALUES(24,X'00000C2600');
INSERT INTO "search_index_docsize" VALUES(25,X'0000061800');
INSERT INTO "search_index_docsize" VALUES(26,X'0000041300');
INSERT INTO "search_index_docsize" VALUES(27,X'0000071800');
INSERT INTO "search_index_docsize" VALUES(28,X'0000051700');
INSERT INTO "search_index_docsize" VALUES(29,X'0000071A00');
INSERT INTO "search_index_docsize" VALUES(30,X'0000061F00');
INSERT INTO "search_index_docsize" VALUES(31,X'0000071600');
INSERT INTO "search_index_docsize" VALUES(32,X'00000C2500');
INSERT INTO "search_index_docsize" VALUES(33,X'0000062900');
INSERT INTO "search_index_docsize" VALUES(34,X'0000093C00');
INSERT INTO "search_index_docsize" VALUES(35,X'00000D3B00');
INSERT INTO "search_index_docsize" VALUES(36,X'0000073300');
INSERT INTO "search_index_docsize" VALUES(37,X'0000053600');
INSERT INTO "search_index_docsize" VALUES(38,X'0000093800');
INSERT INTO "search_index_docsize" VALUES(39,X'0000092C00');
INSERT INTO "search_index_docsize" VALUES(40,X'0000092800');
INSERT INTO "search_index_docsize" VALUES(41,X'0000086800');
INSERT INTO "search_index_docsize" VALUES(42,X'0000095C00');
INSERT INTO "search_index_docsize" VALUES(43,X'0000073100');
INSERT INTO "search_index_docsize" VALUES(44,X'0000073C00');
INSERT INTO "search_index_docsize" VALUES(45,X'0000053E00');
CREATE TABLE 'search_index_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
INSERT INTO "search_index_idx" VALUES(1,X'',2);
INSERT INTO "search_index_idx" VALUES(1,X'30657870',4);
INSERT INTO "search_index_idx" VALUES(1,X'30707572',6);
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
INSERT INTO "sources" VALUES(1,'fcc_fact_sheet_doc_420034','FCC Updates Covered List to Include Foreign-Made Consumer Routers, Prohibiting Approval of New Models','Federal Communications Commission','Fact Sheet','DOC-420034','WC Docket No. 18-89','2026-03-23','https://docs.fcc.gov/public/attachments/DOC-420034A1.pdf','2026-07-09',1,'primary','FCC fact sheet explaining the Covered List update for foreign-produced consumer routers, impact on new authorizations, continued use of existing routers, and Conditional Approval route.','Use for consumer-facing explanation of what changed, what is not banned, and FCC equipment authorization impact.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(2,'fcc_da_26_278_router_public_notice','FCC''s Public Safety and Homeland Security Bureau Announces Addition of Routers Produced in Foreign Countries to FCC Covered List','Federal Communications Commission','Public Notice','DA 26-278','WC Docket No. 18-89','2026-03-23','https://docs.fcc.gov/public/attachments/DA-26-278A1.pdf','2026-07-09',1,'primary','Public Notice adding routers produced in a foreign country to the Covered List except routers granted Conditional Approval by DoW or DHS.','Use as the base legal source for the router Covered List entry and Conditional Approval process.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(3,'fcc_da_26_286_initial_router_update_waiver','OET Announces Waiver of Prohibitions on Certain Class I Permissive Changes to Covered Routers','Federal Communications Commission','Public Notice','DA 26-286','ET Docket No. 21-232','2026-03-23','https://docs.fcc.gov/public/attachments/DA-26-286A1.pdf','2026-07-09',1,'primary','Initial router waiver allowing certain software and firmware updates for already-authorized covered routers through March 1, 2027; later extended and expanded by DA 26-454.','Use for history of the initial update waiver; prefer DA 26-454 for current update-waiver status.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(4,'fcc_da_26_454_update_waiver_extension','OET Announces Extension and Expansion of Waiver for Certain Software and Firmware Permissive Changes to Covered UAS, UAS Critical Components, and Routers','Federal Communications Commission','Public Notice','DA 26-454','ET Docket No. 21-232','2026-05-08','https://docs.fcc.gov/public/attachments/DA-26-454A1.pdf','2026-07-09',1,'primary','Extends and expands software/firmware update waivers through at least January 1, 2029 for covered routers authorized before March 23, 2026.','Use for update availability and current software/firmware waiver through at least January 1, 2029.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(5,'fcc_da_26_351_conditional_netgear_adtran','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-351','WC Docket No. 18-89','2026-04-14','https://docs.fcc.gov/public/attachments/DA-26-351A1.txt','2026-07-09',1,'primary','First router Conditional Approvals, including specified Netgear and Adtran router classes.','Use for Netgear and Adtran conditional approval dates and scopes.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(6,'fcc_da_26_390_conditional_eero','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-390','WC Docket No. 18-89','2026-04-22','https://docs.fcc.gov/public/attachments/DA-26-390A1.txt','2026-07-09',1,'primary','Adds eero/Amazon Leo router Conditional Approvals, with dates reflected in the FCC appendix.','Use for eero conditional approval scope and dates.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(7,'fcc_da_26_542_conditional_calix_alpha','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-542','WC Docket No. 18-89','2026-06-01','https://docs.fcc.gov/public/attachments/DA-26-542A1.pdf','2026-07-09',1,'primary','Adds Calix and Alpha Networks router Conditional Approvals to the Covered List appendix.','Use for Calix and Alpha Networks conditional approval scopes and dates.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(8,'fcc_da_26_548_conditional_sagemcom','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-548','WC Docket No. 18-89','2026-06-04','https://docs.fcc.gov/public/attachments/DA-26-548A1.pdf','2026-07-09',1,'primary','Adds Sagemcom USA FAST router Conditional Approvals.','Use for Sagemcom conditional approval models and end date.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(9,'fcc_da_26_584_conditional_miri','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-584','WC Docket No. 18-89','2026-06-12','https://docs.fcc.gov/public/attachments/DA-26-584A1.pdf','2026-07-09',1,'primary','Adds Miri Technologies Miri X10 Travel router Conditional Approval.','Use for Miri X10 Travel router conditional approval.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(10,'fcc_da_26_585_conditional_arcadyan','Conditional Approval of Certain Routers and UAS and Exemption from FCC Covered List','Federal Communications Commission','Public Notice','DA 26-585','WC Docket No. 18-89','2026-06-12','https://docs.fcc.gov/public/attachments/DA-26-585A1.pdf','2026-07-09',1,'primary','Adds Arcadyan router Conditional Approvals covering specified T-Mobile 5G FWA, AT&T BGW 720, and Verizon devices.','Use for Arcadyan conditional approval scope and end date.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(11,'fcc_da_26_491_att_hardware_waiver','AT&T Services Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Federal Communications Commission','Order','DA 26-491','ET Docket No. 21-232','2026-05-15','https://docs.fcc.gov/public/attachments/DA-26-491A1.pdf','2026-07-09',1,'primary','Grants AT&T a limited waiver for targeted Class I and Class II hardware permissive changes to covered routers for one year.','Use for AT&T limited hardware-change waiver.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(12,'fcc_da_26_571_ncta_hardware_waiver','NCTA Petition for Expedited Waiver to Permit Targeted Hardware Changes to Covered Routers','Federal Communications Commission','Order','DA 26-571','ET Docket No. 21-232','2026-06-09','https://docs.fcc.gov/public/attachments/DA-26-571A1.pdf','2026-07-09',1,'primary','Grants NCTA member suppliers a limited waiver for specified hardware substitutions in existing authorized covered routers.','Use for NCTA member ISP/supplier hardware waiver.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(13,'fcc_da_26_572_sercomm_hardware_waiver','Sercomm Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Federal Communications Commission','Order','DA 26-572','ET Docket No. 21-232','2026-06-09','https://docs.fcc.gov/public/attachments/DA-26-572A1.pdf','2026-07-09',1,'primary','Grants Sercomm a limited waiver for end-of-life component changes in existing authorized covered routers.','Use for Sercomm hardware waiver.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(14,'fcc_da_26_641_verizon_hardware_waiver','Verizon Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Federal Communications Commission','Order','DA 26-641','ET Docket No. 21-232','2026-06-26','https://docs.fcc.gov/public/attachments/DA-26-641A1.pdf','2026-07-09',1,'primary','Grants Verizon a limited waiver for memory-related, substrate, and end-of-life component changes for covered routers for one year.','Use for Verizon hardware waiver.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(15,'fcc_da_26_642_arcadyan_hardware_waiver','Arcadyan Technology Corporation Petition for Expedited Waiver for Targeted Hardware Changes to Covered Routers','Federal Communications Commission','Order','DA 26-642','ET Docket No. 21-232','2026-06-26','https://docs.fcc.gov/public/attachments/DA-26-642A1.pdf','2026-07-09',1,'primary','Grants Arcadyan a limited waiver for targeted Class I and Class II permissive hardware changes to consumer-grade routers with existing equipment authorizations.','Use for Arcadyan hardware waiver.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(16,'fcc_doc_422746_fnprm_component_rules','Protecting Against National Security Threats to the Communications Supply Chain Through the Equipment Authorization Program - Further Notice','Federal Communications Commission','Fact Sheet / Further Notice','DOC-422746','ET Docket No. 21-232','2026-07-01','https://docs.fcc.gov/public/attachments/DOC-422746A1.pdf','2026-07-09',1,'primary','July 2026 item proposing broader component-related rules and proposing to codify/make permanent certain software and firmware waivers.','Use for proposed future rule changes and public-comment status, not as final law.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(17,'fcc_da_26_673_current_covered_list_july_7','Covered List Updated July 7, 2026','Federal Communications Commission','Public Notice / Covered List Appendix','DA 26-673','WC Docket No. 18-89','2026-07-07','https://docs.fcc.gov/public/attachments/DA-26-673A1.pdf','2026-07-09',1,'primary','Appendix A lists the Covered List as updated July 7, 2026 and includes the router entry dated March 23, 2026.','Use for the latest covered-list snapshot included in this data set.','2026-07-09T18:53:42Z');
INSERT INTO "sources" VALUES(18,'fcc_covered_list_web_page','FCC Covered List and Conditional Approvals Web Page','Federal Communications Commission','Web Page',NULL,'WC Docket No. 18-89','2026-07-07','https://www.fcc.gov/supplychain/coveredlist','2026-07-09',1,'primary','FCC public page where the current Covered List and router Conditional Approvals are published.','Use for live/current lookup; this database should be refreshed against this page before launch.','2026-07-09T18:53:42Z');
CREATE TABLE update_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    frequency TEXT NOT NULL,
    instructions TEXT NOT NULL,
    last_checked TEXT,
    next_check_hint TEXT
);
INSERT INTO "update_jobs" VALUES(1,'FCC Covered List web page','weekly and after FCC Public Notice releases','Check https://www.fcc.gov/supplychain/coveredlist for changed Covered List entries and Conditional Approval tables. Update sources, covered_list_entries, and conditional_approvals.','2026-07-09','Next check within 7 days or immediately after a new DA release.');
INSERT INTO "update_jobs" VALUES(2,'FCC ET Docket No. 21-232 waiver activity','weekly','Search new FCC OET orders for hardware or software/firmware waivers affecting covered routers.','2026-07-09','Next check within 7 days.');
INSERT INTO "update_jobs" VALUES(3,'FCC WC Docket No. 18-89 Covered List activity','weekly','Search new FCC PSHSB public notices for Covered List updates and Conditional Approvals.','2026-07-09','Next check within 7 days.');
INSERT INTO "update_jobs" VALUES(4,'Conditional approval expirations','daily','Trigger website alerts 180, 90, 30, and 7 days before approval_end_date.','2026-07-09','Can be automated from vw_expiring_soon_conditional_approvals.');
INSERT INTO "update_jobs" VALUES(5,'Waiver expirations','daily','Trigger website alerts 180, 90, 30, and 7 days before effective_end_date.','2026-07-09','Can be automated from vw_active_waivers.');
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
INSERT INTO "waivers" VALUES(1,'software_firmware','All covered-router producers for previously authorized covered routers','Routers produced in a foreign country and authorized for use in the United States before the March 23, 2026 Covered List addition.','Class I and analogous Class II software and firmware updates that mitigate harm to U.S. consumers, including functionality, vulnerability patches, and operating-system compatibility.','2026-05-08','2026-05-08','2029-01-01','active','Applies to software/firmware changes that mitigate harm; does not generally include hardware changes.','Consumers should continue applying legitimate router firmware/security updates from their manufacturer or ISP.',4,'2026-07-09');
INSERT INTO "waivers" VALUES(2,'software_firmware','All covered-router producers for previously authorized covered routers','Routers produced in a foreign country and authorized for use in the United States before the March 23, 2026 Covered List addition.','Initial Class I software and firmware permissive changes that mitigate harm.','2026-03-23','2026-03-23','2027-03-01','superseded','Superseded by DA 26-454 extension/expansion through at least January 1, 2029.','Historical context only; use DA 26-454 for the current update-waiver rule.',3,'2026-07-09');
INSERT INTO "waivers" VALUES(3,'hardware','AT&T Services','Targeted hardware changes to covered routers with existing equipment authorizations.','Targeted Class I and Class II permissive hardware changes allowed by the AT&T waiver order.','2026-05-15','2026-05-15','2027-05-15','active','Limited to waiver scope; not a general authorization of all hardware changes or new covered models.','May reduce risk of AT&T broadband equipment supply disruption.',11,'2026-07-09');
INSERT INTO "waivers" VALUES(4,'hardware','NCTA member ISPs and their suppliers','Covered routers with existing equipment authorizations used by NCTA member suppliers.','Limited substitutions involving substrate materials and memory modules, as described in the order.','2026-06-09','2026-06-09','2027-06-09','active','Partially granted; limited to specified circumstances and period.','May reduce disruption for ISP-supplied broadband routers.',12,'2026-07-09');
INSERT INTO "waivers" VALUES(5,'hardware','Sercomm Corporation','Sercomm covered routers with existing equipment authorizations.','End-of-life component changes as described in the order.','2026-06-09','2026-06-09','2027-06-09','active','Limited to waiver scope and period.','May preserve availability of affected broadband equipment.',13,'2026-07-09');
INSERT INTO "waivers" VALUES(6,'hardware','Verizon','Covered routers with existing equipment authorizations used by Verizon.','Memory-related, substrate, and end-of-life component changes described in the order.','2026-06-26','2026-06-26','2027-06-26','active','Limited to waiver scope and period.','May reduce disruption for Verizon broadband equipment.',14,'2026-07-09');
INSERT INTO "waivers" VALUES(7,'hardware','Arcadyan Technology Corporation','Consumer-grade routers with existing equipment authorizations that are produced in foreign countries and are on the Covered List.','Targeted Class I and Class II permissive hardware changes described in the order.','2026-06-26','2026-06-26','2027-06-26','active','Limited to waiver scope and period; not a general exemption.','May reduce disruption for affected Arcadyan-supplied routers.',15,'2026-07-09');
INSERT INTO "waivers" VALUES(8,'software_firmware','Commission-wide rulemaking proposal','Covered routers and certain covered UAS/UAS components.','Proposal to codify and make permanent software and firmware waivers that mitigate harm.','2026-07-01',NULL,NULL,'proposed','Proposed in a rulemaking/further notice; not final in this data set.','Consumer-facing language should say this is proposed, not adopted.',16,'2026-07-09');
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
PRAGMA writable_schema=OFF;
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('sources',18);
INSERT INTO "sqlite_sequence" VALUES('regulatory_events',15);
INSERT INTO "sqlite_sequence" VALUES('covered_list_entries',1);
INSERT INTO "sqlite_sequence" VALUES('definitions',6);
INSERT INTO "sqlite_sequence" VALUES('conditional_approvals',11);
INSERT INTO "sqlite_sequence" VALUES('waivers',8);
INSERT INTO "sqlite_sequence" VALUES('consumer_faqs',7);
INSERT INTO "sqlite_sequence" VALUES('claims',6);
INSERT INTO "sqlite_sequence" VALUES('audience_segments',5);
INSERT INTO "sqlite_sequence" VALUES('checklist_items',10);
INSERT INTO "sqlite_sequence" VALUES('alerts',4);
INSERT INTO "sqlite_sequence" VALUES('content_pages',5);
INSERT INTO "sqlite_sequence" VALUES('api_examples',8);
INSERT INTO "sqlite_sequence" VALUES('update_jobs',5);
INSERT INTO "sqlite_sequence" VALUES('data_notes',6);
COMMIT;
