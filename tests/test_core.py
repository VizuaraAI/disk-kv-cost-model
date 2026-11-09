"""Checks that need no GPU. Run with: python tests/test_core.py

They confirm that the fits reproduce the lab note from the logged rows, that the traces match their hashes, and that the
code runs with and without the MLA rows."""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import costmodel as C  # noqa: E402


def near(a, b, tol, what):
    assert abs(a - b) <= tol, f"{what}: got {a}, expected {b}"


def main():
    for line in (C.DATA / "traces" / "SOURCE.txt").read_text().splitlines():
        m = re.match(r"(\S+\.jsonl): size (\d+), sha256 (\w+)", line)
        if m:
            data = (C.DATA / "traces" / m.group(1)).read_bytes()
            assert hashlib.sha256(data).hexdigest() == m.group(3), "trace changed: " + m.group(1)

    without = C.load_rows(False)
    assert len(C.valid_hits(without)) == 158, len(C.valid_hits(without))
    s = C.summary(without, "local")
    assert s["designs"] == ["gqa", "mha"] and s["cells"] == 14 and s["correct"] == 14 and s["load_cells"] == 0
    near(s["T0_ratio"], 1.07, 0.005, "T0 ratio without MLA, local")

    if C.has_mla():
        full = C.load_rows(True)
        assert len(C.valid_hits(full)) == 228, len(C.valid_hits(full))
        loc, vol = C.summary(full, "local"), C.summary(full, "volume")
        near(loc["T0_by_design_ms"]["gqa"], 27.6, 0.05, "T0 GQA")
        near(loc["T0_by_design_ms"]["mha"], 29.5, 0.05, "T0 MHA")
        near(loc["T0_by_design_ms"]["mla"], 60.8, 0.05, "T0 MLA")
        near(loc["T0_ratio"], 2.20, 0.005, "T0 ratio, local")
        near(loc["mean_abs_pct_error"], 13.2, 0.05, "hit error, local")
        near(loc["B_GBps"], 2.19, 0.005, "B, local")
        near(vol["T0_ratio"], 6.7, 0.05, "T0 ratio, Volume")
        near(vol["mean_abs_pct_error"], 43.7, 0.05, "hit error, Volume")
        assert loc["correct"] == vol["correct"] == 21 and loc["load_cells"] == vol["load_cells"] == 0
        print("reproduced the lab note, MLA rows included")
    else:
        print("MLA rows are not in this copy, so the three-design numbers were not checked")
    print("all checks passed")


if __name__ == "__main__":
    main()
