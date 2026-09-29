from __future__ import annotations
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data/processed/fig2_promotion_20260929/pathway_endpoint_promotion.csv"

def test_fig2_promotion_matrix_is_current() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_fig2_promotion_matrix.py"), "--check"],
        cwd=ROOT, check=True,
    )

def test_fig2_promotion_matrix_has_12_cells_and_expected_gaps() -> None:
    with MATRIX.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 12
    keyed = {(r["pathway"], r["endpoint"]): r for r in rows}
    assert keyed[("direct_return", "yield")]["independent_trial_keys"] == "11"
    assert keyed[("direct_return", "N2O")]["gap_to_10"] == "7"
    assert keyed[("biochar_return", "CH4")]["gap_to_10"] == "6"
    assert keyed[("open_burning", "N2O")]["gap_to_10"] == "8"
    assert all(r["inference_guardrail"] == "screening_target_only_not_model_readiness" for r in rows)
