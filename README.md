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

The current research question, three-pathway scope, data layers, analysis
gates, six-figure plan, and next milestones are documented in the
**[project framework and analysis plan](docs/PROJECT_FRAMEWORK_AND_ANALYSIS.md)**
(Chinese). Scope, data, method, figure, or conclusion changes must update that
document and append a dated entry to the **[project change log](docs/PROJECT_CHANGELOG.md)**
in the same commit. Older exploration notes remain available for provenance
but are not automatically current conclusions.

The project now includes a compact full-text-reviewed evidence snapshot at
[`literature/evidence_database.csv`](literature/evidence_database.csv): 438 paired
effects from 26 independent field experiments. The row is a treatment–control
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
field experiments alongside the subset passing the row-level variance-origin
screen. Its threshold flag is not a substitute for statistical or
system-boundary checks.
