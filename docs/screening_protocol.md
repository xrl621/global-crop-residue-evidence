# Literature screening protocol (v1)

Use `literature/screening_template.csv` as the article-level screening log. It
is deliberately separate from `literature/evidence_database.csv`, which holds
multiple numeric contrasts per accepted field experiment. Never turn one
screening row directly into one meta-analysis effect.

## Decision sequence

1. Register DOI, title, authors, publication year, search source and search
   date. Normalize DOI before de-duplication, but preserve all source records
   with a shared `duplicate_group`.
2. At title/abstract stage, mark `screening_stage=title_abstract` and
   `decision=include`, `exclude`, or `hold`. `hold` means information is
   insufficient, not a negative study result.
3. At full text, confirm a real field experiment in a core food crop; identify
   the residue feedstock, management pathway, matched control, measured
   outcome, treatment/control arm means, arm uncertainty and replicate count.
   Record the local full-text location without uploading the PDF by default.
4. Resolve whether several papers, seasons, doses or sites represent the same
   independent field experiment. Use `duplicate_group` plus a study key in the
   numeric extraction, not publication count, to prevent pseudoreplication.
5. Record `decision=include`, `exclude`, or `hold` with a concise reason.
   Include only explicitly matched, traceable contrasts in the numeric formal
   layer; retain incomplete records in screening or candidate layers.

## Suggested controlled values

| Field | Suggested values or rule |
| --- | --- |
| `screening_stage` | `title_abstract`, `fulltext`, `data_extraction` |
| `decision` | `include`, `exclude`, `hold` |
| `field_experiment` | `yes`, `no`, `unclear`; pots and lab incubations are not main field trials. |
| `pathway_candidate` | `direct_return`, `biochar_return`, `open_burning`, `other`, `unclear` |
| `arm_means_available`, `arm_uncertainty_available`, `independence_resolved` | `yes`, `no`, `unclear` |
| `exclusion_reason` | Examples: `not_field`, `not_core_crop`, `no_matched_control`, `duplicate_experiment`, `outcome_not_relevant`, `uncertainty_unrecoverable`. |

Reviewers should not infer `yes` from a secondary database's non-empty numeric
cell. Use primary methods, tables, figure captions and supplementary material
to confirm what each number and error bar means. When several papers use the
same trial, record each article but give their extracted effects the same
independent study key.
