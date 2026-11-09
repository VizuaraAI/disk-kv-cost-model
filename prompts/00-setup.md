Read README.md, costmodel.py and the section "In short" of docs/exp01-results.md first.

Create a Python virtual environment in .venv with Python 3.11 or newer. Install with `pip install --require-hashes -r requirements.lock.txt`. If a package has no build for this machine, say so and stop. Do not fall back to unpinned versions without asking me. On Colab, use the same command in a fresh runtime.

Run `python tests/test_core.py` and `python costmodel.py`. Tell me whether the tests pass, and whether the MLA rows are present in this copy.

Then explain to me, in six plain sentences: what T0, k and B each stand for; what a leave-one-design-out test does; what the rule required of G1 and why it failed on each tier; why 21 of 21 decisions tells us little here; what the difference is between what the rule decided and what we read afterward; and why any number computed from these rows is post hoc for Exp01.

Do not change costmodel.py or anything in data/.
