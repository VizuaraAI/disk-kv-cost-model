Ablation B: where the load-or-recompute decision could go either way. This needs no GPU and runs on a laptop in a few minutes.

Read README.md, costmodel.py and the sections "Main table", "Gates" and "Controls" of docs/exp01-results.md first. Write ablations/b_mix.py. Import from costmodel.py and do not modify it.

The question: recompute won all 21 cells on both tiers, so always answering recompute scores the same as the model. What bandwidth or GPU speed would make the decisions mix, so that an accuracy test has power? And inside that region, how many decisions does the T0 error change?

Before any analysis, write ablations/B/decision_rule.json, save its SHA-256 to ablations/B/decision_rule.sha256, and have the analysis refuse to run if the file has changed. Include in it, in my words, what I expect to happen and why. Define "has power" there: I suggest that the always-majority baseline scores at most 15 of 21, so that at least 6 cells go each way, but the choice is mine and must be fixed before the sweep. State that this is post hoc and a calculation from fitted terms.

Step 1. The bandwidth each cell needs. For each design and length on the local tier, solve T0 + k * L / 256 + L * b / B = T_rep(L + 16) for B, using the joint fit and each design's recompute fit, and report where no bandwidth can win because T0 and k alone exceed recompute. Report the table beside the measured 3.39 GB/s cold read, the fitted 2.19 GB/s and about 28 GB/s for pinned host-to-GPU copies.

Step 2. The sweep. Take a virtual tier with B from 0.25 to 64 GB/s, on a log grid of 25 points, and a virtual slower GPU that multiplies recompute time by s in {1, 2, 4}. The factor s is a stand-in for a slower GPU and is not a measurement of any GPU. For each (B, s), predict the decision in all cells, once with the shared T0 and once with each design's own T0, with k fixed at the joint fit. Save a heatmap of the number of "load" cells, and mark the region that has power under my rule.

Step 3. What the T0 error changes. In each cell of the sweep, count the decisions that differ between the shared T0 and the per-design T0. Report the maximum and the typical count inside the region with power. Then repeat with an error in B of plus and minus 30%, so that a reader can compare how much each term matters to the decision.

Step 4. The real flips. Exp01 has a few measured cases that are not one-sided. GQA with FP8 on the local disk crosses near 28,300 tokens. The `ctl_warm` rows (warm page cache) and `ctl_cpu` rows (CPU tier) give other load times for the same request at 4,096 and 32,000 tokens. Tabulate measured recompute, disk hit, warm hit and CPU hit for each, and say whether the model fitted on the disk hits gets each decision right when given the tier's own bandwidth, which you should take from the measured bytes and time. There are few of these, and some are single rows, so say so. Control: at each design's own point (B = 2.19, s = 1), your sweep must predict recompute in all 21 cells, matching the registered result. Stop and tell me if it does not.

Step 5. What to measure next. Write two short paragraphs in NOTES.md with numbers. Which real tier and GPU would give a test with power under my rule? Which of them can we rent, as far as the review says? Do not invent prices or drive ratings. If you need one that the review does not give, leave it as a question for me.

If data/pending_mla/ is absent, use GQA with FP8 as the third byte size and say that the sweep then has one design at two sizes, which is a weaker test of transfer across designs.

Save results/ablations/B/table.csv, needed_bandwidth.csv, decisions_heatmap.png, t0_flips.png and results/ablations/B/NOTES.md. In the notes, give the verdict of my rule first. The limits to state: every cell of the sweep is a prediction from terms fitted at one bandwidth, k may change with the tier, as the Volume showed, and a real tier may break the linear form. Do not modify data/. Finish by printing the main table and three bullet points with the key numbers.
