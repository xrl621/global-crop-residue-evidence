"""Fetch and verify Smerald's public default cereal-residue NetCDF.

The RADAR landing page records the dataset DOI and lists the source files.
This script downloads only the authors' default mean dataset, not the 18
alternative assumption combinations or the full 1.1-GB archive.
"""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data/external/smerald2023_residue_management/crop_residue_usage_mean.nc"
URL = (
    "https://radar.kit.edu/radar-backend/archives/oYtWbDCHbOmIyUQr/"
    "retrieveFile/IVNoqDFYSxSaPabV"
)
EXPECTED_MD5 = "f860dd189990126277d5911024347877"


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists():
        actual = md5(DESTINATION)
        if actual != EXPECTED_MD5:
            raise ValueError(f"Existing source MD5 differs from RADAR: {actual}")
        print(f"Verified existing file: {DESTINATION.name}")
        return
    partial = DESTINATION.with_name(DESTINATION.name + ".part")
    if partial.exists():
        raise FileExistsError(f"Inspect partial download before retry: {partial}")
    try:
        with urllib.request.urlopen(URL, timeout=180) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = md5(partial)
        if actual != EXPECTED_MD5:
            raise ValueError(f"Downloaded source MD5 differs from RADAR: {actual}")
        partial.replace(DESTINATION)
        print(f"Downloaded and verified: {DESTINATION.name}")
    except Exception:
        print(f"Download incomplete; inspect temporary file: {partial}")
        raise


if __name__ == "__main__":
    main()
