# Agent: Driver distraction

Constrain interaction so the assistant never demands visual-manual attention while driving.

1. Fetch the synthesis output and the `distraction` pack in parallel.
2. Fetch register and inbox in parallel.
3. One finding per theme. Propose SYS-DIST and SYS-HMI requirements not already covered: voice-only completion, short interruptible prompts, lockouts, high-impact confirmation, workload-aware timing (COG-13), conversation yielding to driving (COG-17).
4. List items touching COG-12, COG-13, COG-16, COG-17 in `metrics.review_items`.

Cite ISO 15005 and NHTSA visual-manual themes.
