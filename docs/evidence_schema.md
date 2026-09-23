# Evidence database schema (v1)

`literature/evidence_database.csv` is a compact, machine-readable projection of
the local full-text-validated effect table. It is **not** the raw extraction
file and must not be interpreted as one independent study per row. Each row is
one treatment–control contrast for one outcome at a reported observation
time, season, soil depth, or treatment dose. `study_id` is the field-experiment
cluster used for statistical independence; multiple rows can share a control
and a study. The current snapshot contains 428 effects from 26 independent
field experiments.

## Scope and analysis rules

- Core pathways: `direct_return`, `biochar_return`, `open_burning`. Removal or
  no-residue management is a common comparator, not a fourth intervention
  pathway.
- The current outcome codes are `yield`, `SOC`, `CH4`, `N2O`, `GWP`, `GHGI`,
  `SOC_sequestration_rate`, and `net_GWP_SOC_adjusted`. Do not
  pool unlike endpoints simply because they share a broad theme.
- The sign of `lnrr` is treatment relative to the matched control. A positive
  yield `lnrr` is increased yield; a positive GHG `lnrr` is increased emissions.
- Repeated years, seasons, doses, depths, and shared controls are dependent.
  Never use the 428 rows as 428 independent studies. For a first pathway ×
  outcome pooled model, require at least 10 independent `study_id` values.
- GWP conversion factors and system boundaries differ across source papers.
  `gwp_version` and `system_boundary` must be harmonized before cross-paper
  GWP synthesis. Soil-only GHG results exclude open-burning pulses unless the
  source explicitly says otherwise.
- SOC-related source measurements can include organic-matter proxies. Inspect
  `soc_measure`, `soil_depth`, and the source paper before converting them to
  absolute SOC stock or combining them with direct SOC measurements.
- All exported rows have a recorded full-text review and formal admission
  decision. This does not mean identical certainty or automatic main-model
  eligibility: reconstructed, digitized, or secondary-origin uncertainty must
  be checked via `variance_provenance`, `analysis_tier`, `sensitivity_note`,
  and `quality_flags`.

## Fields

| Field | Meaning |
| --- | --- |
| `effect_id` | Unique paired-effect identifier; primary key in this CSV. |
| `study_id` | Independent field-experiment identifier; clustering key for meta-analysis. |
| `paper_doi` | DOI of the primary article, blank when not verified in the source table. |
| `paper_title` | Primary article title as captured in the source table. |
| `citation` | Short author–year citation when available. |
| `publication_year` | Four-digit publication year when available. |
| `experiment_year` | Source observation period; may be a year, season range, or pooled-period label. |
| `country` | Study country as reported or source-site country if present. |
| `location` | Reported site name or locality. |
| `latitude`, `longitude` | Coordinates when present in the validated source table; do not infer missing coordinates from country. |
| `broad_climate`, `koppen_climate` | Source climate descriptors. Missing or unvalidated classes remain blank. |
| `crop_as_reported` | Literal or near-literal crop description, sometimes including rotation context. |
| `crop_core` | Normalized main crop where explicitly verified. |
| `season` | Reported growing or harvest season. |
| `residue_as_reported` | Reported residue or verified biochar feedstock; may be blank. |
| `pathway` | One of the three core management pathways above. |
| `outcome` | Source endpoint mapped to the formal outcome code. |
| `outcome_unit` | Unit of both arm means when supplied; do not assume a unit when blank. |
| `treatment_arm`, `control_arm` | Exact matched management arms or labels. |
| `treatment_mean`, `control_mean` | Positive source arm means used to compute `lnrr`. |
| `treatment_sd`, `control_sd` | Arm SDs used in the sampling variance; their provenance may include SE conversion, figure digitization, or statistical reconstruction. |
| `treatment_n`, `control_n` | Replicate counts for the matched arms, not counts of years or seasons. |
| `lnrr` | Natural log response ratio, `ln(treatment_mean / control_mean)`. |
| `variance_lnrr` | Source-audited sampling variance of `lnrr`; shared-arm covariance is handled at model stage, not by pretending effects are independent. |
| `percent_change` | `100 × (exp(lnrr) − 1)`, recomputed by the export script. |
| `shared_control_group` | Identifier for contrasts sharing a control within a field trial. |
| `source_locator` | Primary paper table, figure or supplementary-data location. |
| `variance_provenance` | Explanation of where SD/SE/variance values came from. |
| `analysis_tier` | Current tier after narrowly scoped reconciliation of three primary-reviewed studies; not a substitute for `formal_decision`. |
| `source_analysis_tier` | Original tier from the local validated source, retained even if it still says `pending`. |
| `tier_reconciliation` | Nonblank only where an original pending label was reconciled against an existing full-text review. |
| `formal_decision` | Full-text review decision and any admission condition. |
| `variance_origin_status` | `unresolved_row_origin` or `documented_or_reconstructed`; this is only a variance-provenance screen, not full model admission. |
| `independence_resolution` | How repeated observations or shared controls were grouped. |
| `sensitivity_note` | Required caveat or model exclusion sensitivity. |
| `quality_flags` | Semicolon-separated unresolved provenance/metadata flags generated without altering the source admission decision. Blank is not a guarantee of absence of all bias. |
| `system_boundary` | Included processes and time/soil boundaries in the reported effect. |
| `gwp_version` | Radiative-forcing factor set used by the source GWP calculation. |
| `soc_measure`, `soil_depth` | Carbon endpoint definition and soil sampling depth. |
| `water_regime` | Reported water or irrigation context. |
| `nitrogen_rate` | Reported nitrogen treatment rate or stratum; source units need checking before quantitative harmonization. |
| `extraction_method` | Table extraction, digitization or other source method where recorded. |

Blank cells mean **not available in the validated source table**, not zero.
Numeric arm means, SDs, replicate counts, `lnrr`, and `variance_lnrr` are
required for every exported row. The export validates positive means and
variance, unique effect IDs, full-text review status, admission decision, and
`lnrr` consistency with the arm means.

In this snapshot, 13 rows lack a title, 6 lack a primary DOI, and 113 lack
both broad and Köppen climate fields. These gaps stay visible rather than
being filled from unverified secondary metadata.

The 2026-09-23 [quality audit](EVIDENCE_QUALITY_AUDIT_20260923.md) first
reconciled 30 of 52 source-table `pending` labels. A subsequent
[primary-table recheck](PRIMARY_TABLE_RECHECK_20260923.md) resolved the row-level
variance source for another 20 effects in two studies. The public CSV retains
the old tier in `source_analysis_tier` and records the reconciliation source.
Only two figure-digitized SOC rows remain `unresolved_row_origin` and are
excluded from the variance-origin-screen count for first-pass inverse-variance
models. Six rows still lack a DOI. Four Yang 2019 yield SDs and their sampling
variances changed when exact primary-table values replaced secondary rounding;
their means and lnRR did not change. `documented_or_reconstructed` does **not**
mean automatic main-model eligibility: dependence, variance reconstruction,
comparator and system boundaries still require review.

## Rebuild and provenance

The complete local audit table remains outside the public repository. When it
is available in the workspace, regenerate and check the compact CSV with:

```bash
python scripts/export_evidence_database.py
python scripts/export_evidence_database.py --check
```

The default source is
`data/formal_analysis_v1/outputs/formal_validated_staging_v0.csv`; a different
validated source can be supplied with `--source`. The repository CSV is a
reviewable snapshot. Reproducing primary extraction still requires access to
the cited articles and the local full audit table. Do not use the unchecked
candidate database as a substitute for the validated source.
