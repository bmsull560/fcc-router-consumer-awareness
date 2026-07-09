# Source and publishing caveats

This repository is a consumer-awareness data seed. Treat it as editorial and technical scaffolding, not a legal compliance system.

Before publishing or making claims that affect buying, selling, importing, or router support decisions:

1. Re-check the live FCC Covered List.
2. Re-check router-related Conditional Approval letters.
3. Re-check active and expired waivers.
4. Re-check FCC Equipment Authorization records for any model-specific claim.
5. Re-run `python3 scripts/validate_db.py` and review updated row counts.

Suggested production practice: show `current_as_of` prominently and include primary-source links on every regulatory-status page.
