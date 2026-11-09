Ablation C: what a scheduler gets from the cost model. This needs no GPU and runs on a laptop in a few minutes.

Read README.md, costmodel.py, section 2.7 of docs/literature-review.md and the bullet of section 8 on where scheduling enters. Write ablations/c_queue.py. Import from costmodel.py and do not modify it.

The question: on one GPU serving two tenants, does a queue benefit from loading hits from disk even when each hit is slower than recompute for its own request? How much of that depends on whether the GPU is free during the read? And how wrong can the cost model be before the schedule changes?

Before any analysis, write ablations/C/decision_rule.json, save its SHA-256 to ablations/C/decision_rule.sha256, and have the analysis refuse to run if the file has changed. Include in it, in my words, what I expect to happen and why, the service targets I choose and why, and the difference in p99 or in target attainment that I would call a real difference on this simulator. State that this is a simulation built on one run's fits, so it can rank options and cannot give production latencies.

The model, all of it simple on purpose.

Traces. Merge data/traces/conversation_trace.jsonl as tenant 0 and data/traces/toolagent_trace.jsonl as tenant 1. Add 1,000,000,000 to tenant 1's hash ids so that the tenants share no blocks. Each hash is a block of 512 tokens. Keep the burst shape, and scale all timestamps by one factor so that always-recompute keeps the GPU busy for a chosen share rho of the time. Use rho in {0.7, 0.95}, and say that the scaling changes the rate and keeps the bursts.

Disk tier. Every block is persisted when first seen. A block counts as a hit if it was seen within the last 15 minutes of scaled time. The hit length h of a request is 512 times the number of leading blocks that hit, capped at L minus 16.

GPU. One GPU runs one prefill at a time, with no batching and no decode. Time to first token is the time from arrival to the end of prefill. Recompute takes T_rep(L). A hit takes a read of k * h / 256 + h * b / B, plus GPU work of T_rep(L) - T_rep(h) + T0. Use the local tier's joint fit for T0, k and B, and each design's own recompute fit.

Reads. Two cases, both labelled as assumptions. In the first, the read holds the GPU. In the second, the read runs off the GPU, and the request joins the GPU queue when its read ends. In the second case, limit concurrent reads to 1, 8 or no limit, with waiting reads served first come, first served. We have not measured which case vLLM is in, and which one holds may decide the outcome. Check whether the code or logs that this repository holds can tell us, and if they cannot, say so and name the measurement that would.

Policies. The decision is one of: always recompute; always load when h > 0; load when the unloaded estimate says it is faster. The order is first come, first served, or shortest predicted GPU work first. Add one aged order of your own design, to protect long requests, and fix its form in the rule before you run it.

Designs. GQA, MHA and GQA with FP8. Add MLA only if data/pending_mla/ exists.

Metrics. Per policy, design and rho: p50 and p99 of time to first token overall and per tenant, attainment of my targets per tenant, GPU busy share, share of requests with h = 0, share of requests that load, and terabytes read per hour.

Controls. Run these first and stop if one fails. (1) GPU busy share under always-recompute must match rho. (2) At very low rho, time to first token must approach service time. (3) On Poisson arrivals with the same request sizes, first come, first served, the mean wait must match the Pollaczek-Khinchine formula within 5%. (4) When reads hold the GPU, GQA's estimate-based decision must equal always-recompute, because recompute won every native GQA cell. (5) With tenant ids swapped, every per-policy result must be unchanged apart from the labels.

Then the accuracy test. A scheduler ranks with a predicted cost and the queue runs on the true cost. Give the scheduler T0 wrong by the factor the rule found, in both directions, and B wrong by plus and minus 30%, in each case for both the order and the load decision. Report how much p99 and target attainment change against a scheduler with the true cost. If a wrong term changes nothing, find out why and report that, because the reason may be in the traces. Look at how many requests share a first block.

Save results/ablations/C/table.csv, ttft_by_policy.png, tenants.png, accuracy.png and results/ablations/C/NOTES.md. In the notes, give the verdict of my rule first. The limits to state: one GPU, no batching and no decode, so waits are far from what a real server shows; fits from one H100 on one day; a trace with no tenant labels of its own, so the two tenants are our construction; about one hour of trace; and reads whose bandwidth stays constant under load. Do not modify data/. Keep all randomness seeded, and finish by printing the main table and three bullet points with the key numbers.
