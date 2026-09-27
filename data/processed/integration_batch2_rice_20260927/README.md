# Rice paired-candidate batch 2

Rebuild with `python scripts/integrate_rice_pairs_batch2.py` using the local inputs
and hashes in `manifest.json`. See [the batch report](../../../docs/BULK_INTEGRATION_BATCH2_RICE_20260927.md).

213 contrasts / 39 source StudyIDs are candidates, not verified independent trials.
846 positive-mean endpoint records are not new primary admissions. Do not add
them to batch-1 source-record totals. Raw values remain separate from primary
mean corrections; missing matching fields and uncertainty provenance are explicit.
No SOC endpoint is supplied. The existing primary master is unchanged.

Full arm tables, contrasts and SQLite stay local pending third-party compilation
licence/deposit review. Tracked coverage and queue metadata are not analysis-ready.
