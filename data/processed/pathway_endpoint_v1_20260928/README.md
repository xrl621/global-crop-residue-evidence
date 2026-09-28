# Separate pathway × endpoint descriptive snapshot

Rebuild with `python scripts/analyze_pathways_separately.py`. Input is the
2026-09-27 strict descriptive snapshot, not the 5,322-row rice external source.
The [analysis note](../../../docs/PATHWAY_ENDPOINT_ANALYSIS_20260928.md) explains
units, exclusions and interpretation. `manifest.json` records input SHA-256,
software versions and output checksums. Trial-level effect IDs and excluded
source rows stay local; summary and comparison-support metadata are tracked.

Medians summarize study × crop effects without inferential intervals. They are
not pooled treatment effects, global predictions or pathway superiority tests.
