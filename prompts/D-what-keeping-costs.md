Ablation D: what keeping the cache costs, per design. This needs no GPU and runs on a laptop in a few minutes.

Read README.md, costmodel.py, section 2.5 of docs/literature-review.md and the section "Dollars" of docs/exp01-results.md first. Write ablations/d_keep.py. Import from costmodel.py and do not modify it.

The question: on real traffic, what hit rate does each design get from a disk tier, at what retention and capacity, and how many terabytes a day does that write? Where does capacity bind, and where does wear?

Before any analysis, write ablations/D/decision_rule.json, save its SHA-256 to ablations/D/decision_rule.sha256, and have the analysis refuse to run if the file has changed. Include in it, in my words, what I expect to happen and why. State which retention I expect to be enough for each trace, and at what capacity each design stops being limited by capacity.

Traces. data/traces/conversation_trace.jsonl and data/traces/toolagent_trace.jsonl, separately. Fields are timestamp in milliseconds, input_length and hash_ids, each hash being a block of 512 tokens. Report their span first, in hours.

Designs. b per token: MHA 524,288, GQA 147,456, GQA with FP8 73,728. Add MLA at 31,104 only if data/pending_mla/ exists. Also add a line at 890 bytes per token labelled as a projection for DeepSeek-V4.1-Flash, from the figure in docs/literature-review.md. We did not run that model.

Simulation. One tier per design and capacity C in {0.5, 1, 2, 4} TiB and also no limit, with LRU eviction by block, an idle time-to-live in {1, 5, 15, 30, 60} minutes and also none. A request's hit length is the longest run of leading blocks that are cached and unexpired. Under the policy "persist every block", every missing block is written at first sight. Under the policy "persist only long prefixes", write only blocks of requests longer than a threshold you choose before the run and state in the rule.

Report per trace, design, capacity and time-to-live: token hit rate, terabytes written per hour of trace and the capacity actually used.

Dollars. Capacity at $0.09 per GiB-month for the Volume and $0.288 per GiB-month for the local disk, from the lab note. Price GPU time at the H100 container rate of $0.00137 per second, also from the lab note. Saved GPU time depends on the case, so report both cases from ablation C: if the read holds the GPU, a hit on a native dtype saves nothing on the local tier, as Exp01 found; if the read runs off the GPU, a hit of h tokens saves T_rep(h) minus T0 of GPU time, using the same service model as ablation C. Report net dollars per hour for each case, and mark which case each row uses.

Wear. Do not invent endurance numbers. Take the drive capacity, its rated drive writes per day, warranty years, write amplification and price as inputs from me, and ask me for them. Until I supply them, report the writes per day that each design needs, and stop there.

Control. With no capacity limit and no time-to-live, the token hit rate cannot exceed one minus the share of tokens in blocks seen for the first time, which you should compute separately and directly. Report the gap, since only leading runs count as hits. With a time-to-live of zero, nothing can hit. With capacity below one request's blocks, the code must not crash and the hit rate must be near zero.

Save results/ablations/D/table.csv, hit_vs_ttl.png (one panel per trace, one line per design), writes_per_hour.png, capacity.png and results/ablations/D/NOTES.md. In the notes, give the verdict of my rule first. The limits to state: about one hour per trace, so a time-to-live beyond about 30 minutes is barely tested and day-scale retention would need an extrapolated tail; each trace on one tier with no other tenants; blocks treated as equal in cost; and a projection line that is no measurement. Do not modify data/. Finish by printing the main table and three bullet points with the key numbers.
