# Persist or Recompute: a bytes-per-token cost model for disk KV caching

A research project in the Vizuara Inference Research Bootcamp (November 2026 to January 2027). The target is a workshop
paper. The candidates are CHEOPS at EuroSys 2027 (first choice, mid-February), HPAI4S at IPDPS 2027 (early February),
EuroMLSys 2027 (late February) and HotStorage 2027 (mid-June). All four dates are expected dates from the 2026 editions.

## The question

When a prompt's KV cache is on disk, a server can load it or recompute it. Loading costs bytes over a bandwidth, and the
bytes per token differ by a large factor between attention designs. We asked whether a cost model with measured terms,
fitted on two designs, predicts the decision and the hit time for a third design it has not seen.

## What we know so far

One experiment, Exp01, on one Modal H100 on 4 November. Three designs: MHA on LongChat-7B (524,288 bytes per token), GQA on
Qwen3-8B (147,456, and 73,728 with FP8) and MLA on DeepSeek-V2-Lite-Chat (31,104). Two tiers: the container's local disk and
a network Volume. Seven lengths from 512 to 32,000 tokens and five prompts per length, with some MHA cells short. The model
is T_load = T0 + k * chunks + L * b / B against T_rep(L) = a * L + c * L^2. The lab note is `docs/exp01-results.md`.

What the rule decided in advance. The gates G0, G1 and the kill clause come from the literature review, applied as written.
Nobody outside the run reviewed them.

- G1 needed at least 19 of 21 decisions, hit error of at most 20% and a T0 ratio below 1.5. It failed on both tiers.
- Local disk: 21 of 21, hit error 13.2%, T0 ratio 2.20, so G1 failed on the T0 clause alone.
- Volume: 21 of 21, hit error 43.7%, T0 ratio 6.7, so G1 failed on two clauses.
- The kill clause (a ratio above 2) fired on both tiers. Its margin on the local disk is small. Its stated reading points to
  the scheduling angle in section 8 of the review.
- Recompute was faster in all 21 cells on both tiers, so always answering recompute also scores 21. The accuracy clause had
  no power, and this run could not test the decision itself on native dtypes.
- A secondary readout registered before the rerun: projecting MHA's local hits from GQA and MLA alone came within 7.4%.

What we read only after the fact, which carries less weight. On the local disk MHA and GQA agree (T0 of 29.5 and 27.6 ms,
bandwidth of 2.05 and 2.01 GB/s) and MLA alone differs (60.8 ms). Much of T0 may be the forward pass over the 16 tail tokens,
which varies by design. This is a hypothesis from one run and we did not test it. The one disk hit that beat recompute was
Qwen3-8B with FP8 at 32,000 tokens.

On measurement. Day 1's 35 GB/s from the local disk was a cache. Evicting it took more than 1 TiB of later writes, and reads
then ran at about 3.4 GB/s. We cannot say from inside the sandbox what serves those reads. LMCache 0.5.6 restored wrong KV in
a smoke test on an L4, for a reason we did not find, so the hits here come from vLLM's native tier.

Limits that apply throughout: one H100, one day, five prompts per cell at most, each hit read once, and no K5, K6 or K7 control
on either MHA arm.

**The MLA rows are in `data/pending_mla/`.** The DeepSeek model carries its own licence, and its use here is under review on
our side. Every script works without that folder. The registered three-design test does not exist without it.

## How we work: agentic-first

Coding is done by an agent, Claude Code or Codex. Your job is to understand each experiment, run it through the agent, check
what comes back and think about what it means.

1. Clone this repository and open a terminal in it.
2. Start the agent here: `claude` for Claude Code, or `codex` for Codex.
3. Paste `prompts/00-setup.md` first. It sets up the environment and checks that our numbers reproduce.
4. Then paste the ablation prompts one at a time. Before each one, read its explanation below and make sure you could defend
   the design to a colleague. Each prompt asks for a decision rule before the analysis. Write your own expectations into it,
   and keep it fixed once the analysis starts.
5. After each one, read the agent's `NOTES.md` and table. If a number looks wrong, ask the agent to check it against the rows.
6. Send us the tables, the figures and a few lines per ablation on what surprised you.

All four run on a laptop or a Colab CPU in minutes. There is no GPU and no cost. Everything they compute from Exp01 is post hoc
for Exp01, because they reuse its data. They can point to what to measure next, and they cannot confirm the claim that failed.

## The ablations, and why each matters for the paper

**A. What is inside T0.** The rule failed on one number, a ratio of 2.20 between fixed costs, and the retest found 3.37 on new
rows (`docs/exp02-retest-results.md`). You put an interval on the T0 ratio across the runs we have, with and without MLA. This
feeds a corrected model.

**B. Where the decision could go either way.** Recompute won every cell, so our accuracy score tells us nothing. You sweep a
virtual tier and a virtual slower GPU to find where the 21 decisions mix, score the model on the few measured cases that did
flip, and count how many decisions the T0 error changes in that region. The answer tells us which hardware a real test needs,
and how much the T0 failure matters for the decision.

**C. What a scheduler gets from the model.** The fallback in the review is scheduling, so this builds a small one. You replay
the two Mooncake traces as two tenants on one GPU, with first-come and shortest-work ordering, at two loads. One assumption
decides a lot here and we have not measured it: whether the GPU is free while a hit is being read. A hit that is slower for its
own request may still free GPU time for the queue. You run both cases, and you test how wrong a cost model can be before the
schedule changes.

**D. What keeping it costs.** You run the same traces through a disk tier per design, across retention times and capacities, and
report hit rate, terabytes written per hour and capacity cost. This is the persist side of the question, and it holds whichever
direction the paper takes. The traces cover about one hour, so retention beyond about 30 minutes is not tested.

## Repository

- `costmodel.py`: the fits, the leave-one-design-out test and the T0 ratio, as in Exp01's analysis. Import from it.
- `data/ttft.csv`: every logged row for MHA and GQA. `mode` is one of `cold`, `cold_tail`, `store`, `hit`, `warmup`, `warmup_hit`,
  `ctl_warm`, `ctl_cpu`, `ctl_gpu` or `ctl_negative`. The lab note explains each.
- `data/pending_mla/`: the MLA rows, and Exp01's full summary, which contains MLA numbers.
- `data/storage.json`: fio and copy bandwidths per tier. `data/traces/`: the Mooncake traces and their hashes.
- `tests/test_core.py`: reproduces the lab note's fits from the rows.
- `prompts/`: the prompts for the agent. `docs/`: the literature review and the lab note.

## Data and licence

LongChat-7B and Qwen3-8B are under Apache 2.0, and the Mooncake traces come from a repository under Apache 2.0. The prompts were wikitext-103
(CC BY-SA 3.0 and GFDL), and no prompt text is in this repository. The code is released under the MIT licence.
