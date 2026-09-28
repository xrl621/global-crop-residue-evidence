"""Download the exact public source files used by OMD residue geography.

Already-present files are verified, not overwritten. A failed/hash-mismatched
download leaves only a temporary .part file and never replaces source data.
"""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    (
        "https://zenodo.org/records/10450921/files/Crop%20residues.csv?download=1",
        ROOT / "data/external/omd2025_crop_residues/Crop residues.csv",
        "0c95f45530631148f02e0a3906a53a60ceae4c1c18700ae05cc70906f6d0dec6",
    ),
    (
        "https://digital-atlas.s3.amazonaws.com/cdh/data/mapspam2020-v2r2/cog/spam2020-production-irrigated.tif",
        ROOT / "data/enrichment/raw/mapspam2020_v2r2/spam2020-production-irrigated.tif",
        "f4e6e4db46dd4f4d27492fa96977baa4cc62f3f33c1a6d09669947c7312fa8fe",
    ),
    (
        "https://digital-atlas.s3.amazonaws.com/cdh/data/mapspam2020-v2r2/cog/spam2020-production-rainfed.tif",
        ROOT / "data/enrichment/raw/mapspam2020_v2r2/spam2020-production-rainfed.tif",
        "8ccd5fc90fbdacaa1d4edc624c76c985ac54d7b5612b73db452539dfc4ffcb5d",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    for url, destination, expected in FILES:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            actual = sha256(destination)
            if actual != expected:
                raise ValueError(f"Existing source has unexpected SHA-256: {destination}: {actual}")
            print(f"Verified: {destination.name}")
            continue
        pending = destination.with_name(destination.name + ".part")
        if pending.exists():
            raise FileExistsError(f"Resolve prior partial download before retry: {pending}")
        try:
            with urllib.request.urlopen(url, timeout=90) as response, pending.open("wb") as output:
                shutil.copyfileobj(response, output)
            actual = sha256(pending)
            if actual != expected:
                raise ValueError(f"Downloaded source has unexpected SHA-256: {destination}: {actual}")
            pending.replace(destination)
            print(f"Downloaded and verified: {destination.name}")
        except Exception:
            print(f"Download incomplete; inspect temporary file: {pending}")
            raise


if __name__ == "__main__":
    main()
