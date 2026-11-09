# Exp02 retest, topic 20: lab note

Run by the Vizuara research team on 7 November 2026 on Modal.

## In short

**The rule's outcome is FIX_SUPPORTED_HIT_TIME.** Every condition in `decision_rule.json` passed and the kill clause did not fire. We replaced the constant T0 with a measured tail term for each design, and on new prompts a model fitted on two designs predicted the third with a hit error of 3.4%. The same rows gave 5.7% with the constant T0 and 10.3% with a sham that gave each design another design's tail.

That outcome is narrower than it may sound, for five reasons that are set out below.

- The margin over the constant T0 is small: 2.3 points against the 2.0 the rule asked for, with an interval of 1.2 to 3.9.
- The fixed-term gate passes because of the 10 ms floor. The raw values are 2.0, 9.0 and 10.5 ms, a ratio of 5.2.
- Reads ran at about 0.63 GB/s, a third of Exp01's speed. We do not know why. With reads this slow, the tail is a small share of most cells.
- k and B fitted on Exp01 missed this run by 62.5%. So these terms have to be measured on the machine in question.
- Recompute won all 21 cells again, so always answering recompute also scores 21. The decision itself has still not been tested.

The Volume was not retested, and its failure stands. Exp01's constant-T0 claim also stays failed: on these new rows its T0 ratio is 3.37, against a limit of 1.5.

One correction to how this was briefed: G1 on the local disk failed on the T0 clause alone. The 13.2% hit error passed its limit of 20%. So this retest had to fix the T0 clause, and lowering the hit error was only part of the test.

## Cost

Modal's billing report for apps named `irb20-exp02` shows **$2.01** ($2.012 over five rows). Our own estimate was $2.05. All five apps are stopped, confirmed with `modal app list`. Volume storage is billed separately and is not in that figure.

By billed cost, the H100 retest was $1.86 for 1,325 seconds of container time, the L4 smoke test $0.10, the Qwen3-8B download and new prompts $0.03, the CPU filler probe $0.02, and a repeat of that probe by hand, which checked the run-once marker and did no work, under $0.01.

## What ran

**Models.** LongChat-7B (MHA, 524,288 bytes per token), Qwen3-8B (GQA, 147,456) and DeepSeek-V2-Lite-Chat (MLA, 31,104) at the same revisions as Exp01. All three were ungated on the Hugging Face API. We downloaded Qwen3-8B into our own volume, with its safetensors hashes checked, rather than read another topic's volume. Those roughly 16 GB stay on `irb20-exp01`.

**Software.** The same lock as Exp01 (`requirements.lock.txt`, SHA-256 `183cb986`), so no package was added. The analysis ran on this Mac in a clean venv built from this repository's `requirements.lock.txt`.

**Workload.** New wikitext prompts starting at character 6,100,000 of the text, where Exp01 stopped at 5,977,352. Seven lengths from 512 to 32,000 tokens, five prompts per length, one output token, temperature 0.

**Protocol.** One H100 container held everything. It wrote 32 GiB as a host check, then stored all three designs, then wrote a sentinel and 1,120 GiB of filler. Then, for each design in turn, a new server read each prompt once and immediately repeated the same request. That repeat has a GPU prefix-cache hit and no load, and its time is the tail. Exp01 used one container per design, so this is a change of protocol, and it is what made the budget fit. The filler used eight fio streams at once in place of one, chosen from a CPU probe of write speed. It took 271 s at 4.45 GB/s.

**The rule.** `decision_rule.json` has SHA-256 `7caabdaa`, and `analyze.py` has `9577ff59`. Both were logged at 00:27 IST on 7 November, before any Modal spend of this experiment (`logs/`). The rule's own text says "about 00:50 IST", which is my mistake, and the log is the record. There are no amendments. The self-test mode of `analyze.py` reproduced 13.2, 8.0, 16.8 and the ratio of 2.20 on Exp01's rows before any new row existed.

## Main table

Times in seconds. The hit is the median over five prompts. "Predicted" is the tail model with that design held out of the fit.

| Length | MHA hit | MHA tail | MHA predicted | GQA hit | GQA tail | GQA predicted | MLA hit | MLA tail | MLA predicted |
|-|-|-|-|-|-|-|-|-|-|
| 512 | 0.450 | 0.0143 | 0.449 | 0.151 | 0.0189 | 0.141 | 0.079 | 0.0440 | 0.074 |
| 1024 | 0.865 | 0.0152 | 0.885 | 0.273 | 0.0221 | 0.267 | 0.110 | 0.0466 | 0.107 |
| 2048 | 1.736 | 0.0160 | 1.755 | 0.523 | 0.0201 | 0.510 | 0.161 | 0.0446 | 0.166 |
| 4096 | 3.451 | 0.0183 | 3.496 | 1.006 | 0.0233 | 1.003 | 0.269 | 0.0454 | 0.287 |
| 8192 | 6.885 | 0.0220 | 6.978 | 2.003 | 0.0250 | 1.985 | 0.493 | 0.0499 | 0.534 |
| 16384 | 13.673 | 0.0326 | 13.944 | 3.905 | 0.0307 | 3.951 | 0.927 | 0.0585 | 1.026 |
| 32000 | 26.636 | 0.0489 | 27.221 | 7.664 | 0.0447 | 7.701 | 1.787 | 0.0694 | 1.960 |

The tail is 44 to 69 ms for MLA, 19 to 45 ms for GQA and 14 to 49 ms for MHA. This is the first measured tail for MHA, where Exp01 used GQA's as a stand-in. MHA's tail turns out close to GQA's, and MLA's is about twice theirs at short lengths. At 4,096 and 32,000 tokens the GQA and MLA tails are 15 to 20% below Exp01's (GQA 23.3 and 44.7 ms against 29.0 and 53.2; MLA 45.4 and 69.4 ms against 54.4 and 82.6).

## Gates

All of this section is pre-registered. Intervals come from 2,000 bootstrap resamples of prompts.

| Gate | Needed | Measured | Interval | Result |
|-|-|-|-|-|
| Admissible | all controls | all pass | | yes |
| R1 hit error | at most 20% | 3.4% | 2.4 to 4.7 | pass |
| R2 against constant T0 | at least 2.0 points better | 2.3 points (5.7% to 3.4%) | 1.2 to 3.9 | pass, narrowly |
| R2 against sham | at least 2.0 points better | 6.9 points (10.3% to 3.4%) | 4.4 to 8.5 | pass |
| R3 fixed-term ratio, 10 ms floor | at most 1.5 | 1.05 | 1.00 to 1.28 | pass |
| R4 worst design | at most 20% | 6.7%, MLA | 4.3 to 9.4 | pass |
| R5 decisions | at least 19 of 21 | 21 | | pass, no power |
| Kill | fixed ratio or B ratio above 2, or under 15 of 21 | 1.05, 1.04, 21 | | does not fire |

Held-out error by design:

| Design | Tail model | Constant T0 | Sham |
|-|-|-|-|
| GQA | 2.0% | 3.9% | 3.9% |
| MHA | 1.5% | 3.3% | 4.8% |
| MLA | 6.7% | 9.9% | 22.2% |

Joint fit of the tail model: k = 1.43 ms per chunk, B = 0.63 GB/s. B by design is 0.636, 0.632 and 0.659 GB/s, a ratio of 1.04.

## How to read that pass

**The floor carries R3.** The fixed term left after the tail is 10.5 ms for GQA, 2.0 ms for MHA and 9.0 ms for MLA. Exp01's rule sets anything below 10 ms to 10 ms, because that is near what this HTTP path resolves, and this rule kept the floor as written. Without it the ratio is 5.2. A fairer way to say it: no design has more than about 10 ms left unexplained, where Exp01's constant model needed 28 to 61 ms. It does not show that the leftovers are equal.

**The original gap repeats and has a different shape.** On the new rows the constant model's T0 is 29.4 ms for GQA, 15.8 ms for MHA and 53.2 ms for MLA, a ratio of 3.37 (interval 2.05 to 5.44). Exp01 said that MHA and GQA agree and that MLA alone sets the gap. Here MHA and GQA differ by a factor of 1.86, so that reading did not repeat.

**Slow reads weaken this test.** The tail is 56% of MLA's hit at 512 tokens and 3.9% at 32,000. For GQA it is 12.5% falling to 0.6%, and for MHA 3.2% falling to 0.2%. So most cells are decided by the bytes term, and the short MLA cells carry most of what the tail does. On Exp01's faster path the fixed term was a larger share of every cell, so a run at that speed would press the tail harder, and this one did not do that.

**Why reads were slow, not known.** Bytes over time to first token at 4,096 tokens and above had a median of 0.61 to 0.63 GB/s for GQA and MHA and 0.54 for MLA, against 1.86, 2.02 and 1.46 in Exp01. vLLM's own read time agrees, so the time is in the file reads. Speed did not drift between the first and second half of each pass. The sentinel's first read was 0.21 GB/s and its re-read 43.8 GB/s, so the reads were cold by the rule. Candidates are this host, the eight filler streams, or one container holding all three stores. We changed all of these at once and tested none of them.

**Terms do not carry between runs.** The secondary readout took k and B from Exp01 and tails from this run, and missed by 62.5% (66% GQA, 68% MHA, 54% MLA). Leaving out one design inside one container works. Taking a bandwidth from another container does not. A cost model of this form has to measure B on the machine in question, and even on the same kind of container on Modal it moved by a factor of three.

**The decision is still untested.** Recompute won all 21 cells, against Exp01's plain-server times and against today's store-pass times. Always answering recompute also scores 21. The measured recompute times come from Exp01, on other prompts. Today's store-pass times, which carry the save path, are within about 17% of them.

## Controls

K3: 105 of 105 hits valid. K4: at most 0.63 GB/s against a limit of 4.236, though this one-sided check says little at these speeds. K6: all 105 repeats show GPU hits and zero external hits. K7: all three negative controls show zero external hits. K8: 105 of 105 first tokens match the store pass, which is better than Exp01's 33 and 34 of 35 on some arms. Sentinel: 0.21 GB/s then 43.8 GB/s.

The negative controls took 0.111, 0.146 and 0.158 s at 4,096 tokens, for MHA, GQA and MLA, against 0.110, 0.106 and 0.058 s in Exp01. This may be the cost of a first request at a new size, which Exp01 also saw. We did not test that.

## What failed

- Nothing in the run itself: all stages completed, the host check passed the first time, the filler did not abort, and all five prompts were read.
- Exp01's constant T0 fails again on new rows, at 3.37.
- Exp01's k and B do not predict this run.
- Exp01's reading that MHA and GQA agree on T0 did not repeat.

## What was not checked

- The Volume. Its result from Exp01 (hit error 43.7%, T0 ratio 6.7) stands as failed, and this fix makes no claim about it.
- The decision on any cell where loading wins. No FP8 arm ran, and FP8 at 32,000 tokens was the only such cell in Exp01.
- K5, the warm page cache and CPU tier ratios.
- Recompute on a plain server with these prompts.
- Why reads ran at 0.63 GB/s, and whether the eight filler streams played a part.
- A second run. This is one H100, one host, one filler, five prompts per cell, each read once.
- A design outside these three. All three were used in Exp01 to suggest the idea, although these prompts and rows are new.
- What the leftover fixed term of up to 10 ms is.
- Whether the GPU is free during a read.
- The DeepSeek licence, which was not legally checked.

## What this means for the paper

This supports a narrow claim: inside one container on one H100, with the tail measured for each design, k and B fitted on two designs predict the third design's hit time within a few percent on the local path. It does not rescue the original claim, and it does not show that the model picks the right tier. The gap that matters most is a tier or GPU where decisions go both ways, which ablation B already looks for at no cost.

Exp01's lab note still says the tail idea is untested. It was written before this run and has not been edited.

## Files

The rule, code, logs and raw rows of this run are not in this repository.
