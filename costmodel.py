"""The cost model of Exp01, from the logged rows. No GPU and no download. Run: python costmodel.py

The fits and the leave-one-design-out test are those of Exp01's analysis, moved here without change. Load time is
T_load = T0 + k * n_chunks + L * b / B, fitted by non-negative least squares on relative error. Recompute time is
T_rep(L) = a * L + c * L^2, fitted the same way on the cold rows.

The MLA rows live in data/pending_mla/. They are read only if that folder exists, and every function here also works
without them. Please do not modify this file. Import from it.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PENDING = DATA / "pending_mla"
LENGTHS = (512, 1024, 2048, 4096, 8192, 16384, 32000)
CHUNK, TAIL = 256, 16
BYTES_PER_TOKEN = {("mha", "auto"): 524288.0, ("gqa", "auto"): 147456.0, ("gqa", "fp8"): 73728.0, ("mla", "auto"): 31104.0}


def has_mla():
    return (PENDING / "ttft_mla.csv").exists()


def load_rows(include_mla=None):
    """All logged rows. include_mla=None means: use the MLA rows if the folder is there."""
    include_mla = has_mla() if include_mla is None else include_mla
    df = pd.read_csv(DATA / "ttft.csv")
    if include_mla:
        df = pd.concat([df, pd.read_csv(PENDING / "ttft_mla.csv")], ignore_index=True)
    return df


def valid_hits(df):
    """Hit rows that pass Exp01's control K3: no GPU prefix hit, the expected external tokens, chunks and bytes."""
    h = df[df["mode"] == "hit"].copy()
    h["b"] = [BYTES_PER_TOKEN[(m, d)] for m, d in zip(h.model, h.dtype)]
    ok = (h.gpu_hits.fillna(0) == 0) & (h.ext_hits == h.L) & (h.n_chunks == h.L / CHUNK) & ((h.bytes_read - h.L * h.b).abs() <= 0.01 * h.L * h.b)
    return h[ok].copy()


def rel_nnls(X, y):
    X, y = np.asarray(X, float), np.asarray(y, float)
    sol, _ = nnls(X / y[:, None], np.ones(len(y)))
    return sol


def fit_rep(cold):
    return rel_nnls(np.c_[cold.L, cold.L.astype(float) ** 2], cold.ttft_s)


def t_rep(ac, L):
    return ac[0] * L + ac[1] * L * L


def cold_fits(df):
    return {key: fit_rep(g) for key, g in df[df["mode"] == "cold"].groupby(["model", "dtype"])}


def fit_load(h):
    t0, k, inv_b = rel_nnls(np.c_[np.ones(len(h)), h.hit_tokens / CHUNK, h.hit_tokens * h.b], h.ttft_s)
    return dict(T0=float(t0), k=float(k), inv_B=float(inv_b))


def predict_load(f, L, b):
    return f["T0"] + f["k"] * (L / CHUNK) + f["inv_B"] * L * b


def per_design_terms(h, k):
    """T0 and B per design with k fixed at the joint fit. This is the T0 of the rule's ratio test."""
    out = {}
    for d, x in h.groupby("model"):
        y = x.ttft_s - k * x.hit_tokens / CHUNK
        A = np.c_[np.ones(len(x)), x.hit_tokens * x.b]
        sol, _ = nnls(A / x.ttft_s.values[:, None], y.values / x.ttft_s.values)
        out[d] = dict(T0=float(sol[0]), inv_B=float(sol[1]), B_GBps=(1 / sol[1] / 1e9 if sol[1] > 0 else math.inf))
    return out


def t0_ratio(terms):
    """The ratio the rule tests. Any T0 below 10 ms is set to 10 ms first, as the rule says."""
    t = [max(v["T0"], 0.010) for v in terms.values()]
    return max(t) / min(t)


def cells(df, hits, model, dtype="auto"):
    """Median measured hit and recompute time per length, for the same request of L plus 16 tokens."""
    out = {}
    c = df[(df.model == model) & (df.dtype == dtype)]
    for L, g in hits[(hits.model == model) & (hits.dtype == dtype)].groupby("L"):
        ct = c[(c["mode"] == "cold_tail") & (c.L == L)].ttft_s
        out[int(L)] = dict(hit=float(g.ttft_s.median()), recompute=float(ct.median()), n_hit=len(g))
    return out


def lodo(df, tier):
    """Leave one design out on one tier, native dtype. One row per design and length, as in the registered test."""
    hits = valid_hits(df)
    h = hits[(hits.tier == tier) & (hits.dtype == "auto")]
    fits = cold_fits(df)
    rows = []
    for held in sorted(h.model.unique()):
        f = fit_load(h[h.model != held])
        b = h[h.model == held].b.iloc[0]
        for L, c in sorted(cells(df, h, held).items()):
            pred = predict_load(f, L, b)
            rep = t_rep(fits[(held, "auto")], L + TAIL)
            rows.append(dict(design=held, L=L, T_hit=c["hit"], T_recompute=c["recompute"], T_hit_pred=pred, T_rep_fit=rep,
                             measured="load" if c["hit"] < c["recompute"] else "recompute", predicted="load" if pred < rep else "recompute"))
    t = pd.DataFrame(rows)
    t["correct"] = t.measured == t.predicted
    t["ape"] = (t.T_hit_pred - t.T_hit).abs() / t.T_hit
    return t


def summary(df, tier):
    hits = valid_hits(df)
    h = hits[(hits.tier == tier) & (hits.dtype == "auto")]
    joint = fit_load(h)
    terms = per_design_terms(h, joint["k"])
    t = lodo(df, tier)
    return dict(tier=tier, designs=sorted(h.model.unique()), T0_ms=joint["T0"] * 1e3, k_ms=joint["k"] * 1e3, B_GBps=(1 / joint["inv_B"] / 1e9 if joint["inv_B"] > 0 else None),
                T0_by_design_ms={d: v["T0"] * 1e3 for d, v in terms.items()}, B_by_design_GBps={d: v["B_GBps"] for d, v in terms.items()}, T0_ratio=t0_ratio(terms),
                cells=len(t), correct=int(t.correct.sum()), load_cells=int((t.measured == "load").sum()), mean_abs_pct_error=float(t.ape.mean() * 100))


if __name__ == "__main__":
    data = load_rows()
    print("MLA rows present:", has_mla())
    for name in ("local", "volume"):
        print(json.dumps(summary(data, name), indent=1))
