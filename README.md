# Global Crop Residue Evidence

A structured research repository for collecting, organizing, analyzing, and visualizing global evidence related to crop residues.

## Repository structure

```text
global-crop-residue-evidence/
├── data/
│   ├── raw/          # Original source data; generally not tracked
│   └── processed/    # Cleaned or analysis-ready datasets
├── scripts/          # Data processing, analysis, and plotting scripts
├── figures/          # Publication and exploratory figures
├── literature/       # Literature notes, evidence tables, and source metadata
├── outputs/          # Generated analysis outputs; generally not tracked
└── docs/             # Project notes, methods, and documentation
```

## Workflow

1. Preserve original source files in `data/raw/`.
2. Record literature and evidence extraction in `literature/`.
3. Clean and harmonize data into `data/processed/`.
4. Keep reproducible analysis code in `scripts/`.
5. Save generated tables, models, and intermediate results in `outputs/`.
6. Save final or reusable visualizations in `figures/`.
7. Document methods, decisions, and conventions in `docs/`.

## Reproducibility principles

- Do not overwrite original raw data.
- Keep transformations reproducible in scripts.
- Use clear file names and stable variable names.
- Record data provenance and source citations.
- Separate manually curated data from automatically generated outputs.

## Status

**2026-09-28: one primary rice trial admitted after Table 2 audit.**
The [source audit](docs/XIONG2015_PRIMARY_EXPANSION_20260928.md) adds 54
paired effects from one three-year field experiment, bringing the reviewed
master to **607 effects / 34 trial keys**. The updated strict descriptive set
is **485 / 27**; 48 of the 54 new effects pass the existing screen, while six
high-relative-error N₂O effects remain traceable but held. The updated
[pathway–endpoint matrix](data/processed/pathway_endpoint_v2_20260928/pathway_outcome.csv)
has 472 core effects / 25 trial keys plus 13 separately audited records.
Two numeric discrepancies in a local secondary rice dataset were resolved
against the publisher's primary Table 2. This is not a global pooled estimate;
the straw feedstock species in this trial is unreported. Run
`python scripts/extract_xiong2015_table2.py`,
`python scripts/export_evidence_database.py --check`,
`python scripts/analyze_stage_evidence.py`, and
`python scripts/analyze_pathways_separately.py` to reproduce the public layer.

**Historical 2026-09-28: analyze each pathway and endpoint first.**
The [separate pathway–endpoint analysis](docs/PATHWAY_ENDPOINT_ANALYSIS_20260928.md)
reorganizes the existing 437-effect strict descriptive snapshot into 18
pathway–endpoint cells and a crop-level evidence grid. It does not require a
paper to report every outcome or all three technologies. Of 437 effects, 424
fit the core crop/endpoint table; 13 remain in a separate-boundary audit.
Trial-level descriptive directions and comparison-support counts are reproducible
with `python scripts/analyze_pathways_separately.py`; they are not pooled estimates
or rankings. At that snapshot the primary master was 553 effects / 33 trial keys.

**2026-09-27: rice arm integration batch 2 (candidate layer only).**
The [batch-2 report](docs/BULK_INTEGRATION_BATCH2_RICE_20260927.md) documents
213 reconstructed contrasts from 39 source StudyIDs, including 25 direct
return-versus-burning contrasts and 846 positive-mean endpoint records.
These are not additional independent trials or primary admissions.
Source-ID collisions, shared controls, missing covariates and prior holds are
explicit; 20 existing primary-reviewed means are linked separately from raw values.
The primary 553/33 and strict descriptive 437/26 snapshots remain unchanged.
Run `python scripts/integrate_rice_pairs_batch2.py` with documented local inputs;
47 tests pass. Full third-party tables and SQLite stay local pending licence review.

**2026-09-27: bulk integration batch 1 (separate from primary admission).**
The [inventory](docs/DATABASE_INVENTORY_AND_SEARCH_20260927.md) distinguishes
12,400 existing secondary candidates from the 553-row reviewed master.
The [bulk-integration report](docs/BULK_INTEGRATION_BATCH1_20260927.md) documents
a local 12,953-record relational database, 96 cross-source paper-identity overlap
groups, and source-level arithmetic/imputation checks on all 153 Lu2020 yield
records. A separate 62-row / 15-paper-cluster secondary descriptive subset is
available locally. **No new primary trial is claimed in this integration batch**;
the 553/33 primary and 437/26 strict descriptive counts below remain unchanged.
Run `python scripts/integrate_evidence_batch1.py` with the documented local inputs.
The full third-party compilation and SQLite stay local pending licence review.

**2026-09-27: primary-source expansion and joint-outcome update completed.**
The [expansion report](docs/DATA_EXPANSION_20260927.md) records 553 paired effects
from 33 trial keys (43 new effects, one new independent trial). The descriptive
set is now 437 effects / 26 trial keys; yield–SOC pairs increased from 15 to 33,
and yield–soil-GWP pairs from 42 to 64. Ten Thailand mean-only effects are retained
separately and are **not** added to the main analysis. The main set still covers
five Asian countries, and one flagged study uses outdoor lysimeters.
See [updated figures](figures/stage_20260927/),
[captions and QA](figures/STAGE_20260927_CAPTIONS_AND_QA.md), and
[source-level provenance](literature/primary_extractions/EXPANSION_20260927_PROVENANCE.md).
Run `python scripts/analyze_stage_evidence.py` and
`python scripts/audit_expansion_20260927.py`; the default output is now dated
20260927, preserving the previous snapshot.

**Historical 2026-09-26 analysis (frozen, superseded by the counts above):**
Read the [results and next priorities](docs/STAGE_RESULTS_20260926.md) and
[six-panel figure notes](figures/STAGE_20260926_CAPTIONS_AND_QA.md).
The new analysis uses the public snapshot only: `python scripts/analyze_stage_evidence.py`.
Reproducible [source-data tables](data/processed/stage_20260926/) retain every
inclusion/exclusion decision and every plotted source effect ID. The screened
descriptive set contains 389 effects from 24 trial keys, all in five Asian
countries; it is **not** a representative global sample or a pooled causal estimate.
The original 510-row snapshot is unchanged. Three assembled figures and six
split panels are provided in [PNG/PDF/SVG](figures/stage_20260926/).

The current research question, three-pathway scope, data layers, analysis
gates, six-figure plan, and next milestones are documented in the
**[project framework and analysis plan](docs/PROJECT_FRAMEWORK_AND_ANALYSIS.md)**
(Chinese). Scope, data, method, figure, or conclusion changes must update that
document and append a dated entry to the **[project change log](docs/PROJECT_CHANGELOG.md)**
in the same commit. Older exploration notes remain available for provenance
but are not automatically current conclusions.

The project includes a compact full-text-reviewed evidence snapshot at
[`literature/evidence_database.csv`](literature/evidence_database.csv): 607 paired
effects from 34 trial keys (2026-09-28 snapshot; not all are open-field trials). The row is a treatment–control
effect, **not** an independent study. See the
[`evidence schema`](docs/evidence_schema.md) for definitions, limitations, and
the study-level analysis rule. New literature can be logged in
[`literature/screening_template.csv`](literature/screening_template.csv) using
the [`screening protocol`](docs/screening_protocol.md).
The [quality audit](docs/EVIDENCE_QUALITY_AUDIT_20260923.md) reconciled 30
legacy labels; the subsequent [primary-table recheck](docs/PRIMARY_TABLE_RECHECK_20260923.md)
resolved another 20 effects against two source papers. Original labels remain
visible. Two figure-digitized SOC effects still lack reproducible row-level
variance provenance and are held out of first-pass inverse-variance counts.
The latest [direct-return primary extraction](docs/DIRECT_RETURN_PRIMARY_EXTRACTION_20260923.md)
adds 10 effects from an already indexed field trial, without inflating the
independent-study count.
The [independent-trial expansion audit](docs/INDEPENDENT_TRIAL_EXPANSION_20260923.md)
adds 26 source-table effects from three new field trials. A further
[Du 2024 extraction and gate re-audit](docs/DU2024_PRIMARY_EXTRACTION_20260923.md)
adds 24 effects from one new wheat trial. Direct-return × yield has 11 trials
in the broad count, but only 8 after excluding three studies with unresolved
reported-error semantics. The subsequent [straw-origin and Table 2 re-audit](docs/STRAW_ORIGIN_AND_RICE140_REAUDIT_20260923.md)
flags a land-clearing-residue trial in both direct-return and burning pathways.
The [burning metadata and error-type re-audit](docs/BURNING_METADATA_AND_GATE_REAUDIT_20260924.md)
then holds one more trial whose published `±` dispersion is not identified as
SD or SE. Subsequent [Nayak and Jijnasa extraction audits](docs/JIJNASA2025_JOINT_YIELD_SOC_AUDIT_20260924.md)
bring current source/core-origin-screened yield coverage to 9 direct-return,
7 biochar and 9 burning trials. The new stage analysis additionally holds the
biochar trial with missing arm labels, leaving 6 biochar trials for the yield
figure. No pathway passes the project's prespecified first pooled-analysis
count gate; that gate alone would not establish a defensible model.

To regenerate the public snapshot from the local full-text-validated audit
table, run `python scripts/export_evidence_database.py`; add `--check` to test
that the committed CSV matches the local source. Primary PDFs, the full audit
table, and automatically generated outputs stay local by default. The CSV is
not a substitute for those source materials or for model-level dependence and
system-boundary checks. Several rows retain unresolved variance-provenance
flags; filter and audit `quality_flags` and `variance_origin_status` before a
submission-grade meta-analysis.

The repository ignore rules keep the pre-repository bulk data, downloaded
papers, generated outputs and exploratory figure files local. Select a final
figure deliberately for version control after checking its data source and
size; it can then be force-added if the ignore rule covers its file type.

For a count-only view of coverage by pathway and outcome, run
`python scripts/describe_evidence.py`. It shows all effects and independent
field experiments alongside variance-origin and stricter uncertainty screens.
The broad threshold flag is not a substitute for statistical or
system-boundary checks.
