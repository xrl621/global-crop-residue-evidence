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

Project scaffold initialized. Detailed study scope, evidence schema, analysis plan, and reproducible workflows can be added as the project develops.
