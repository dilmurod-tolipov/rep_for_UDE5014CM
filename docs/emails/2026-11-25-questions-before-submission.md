# Draft email: questions before the final submission (2026-11-25)

Status: **draft for the student to review and send himself.** Not yet sent.
Figures verified against the committed snapshot of 2026-11-25 before drafting.

---

**To:** Sanjar Bekov (Module Leader)
**Subject:** UDE5014CM Assessment 2 — repository link and five questions before submission (50000161)

Dear Sanjar,

My project is complete on the technical side and I am now preparing the final report. The
repository is:

https://github.com/dilmurod-tolipov/rep_for_UDE5014CM (assessed branch `main`)

The four checkpoint states are tagged, and each one runs from its own commit:

- `cp1` 1cd776dccf36874c03a1b1302659cbaa27cdefe6 — collection MVP (Week 7)
- `cp2` 35ba26068f1a61331d9fcd8f387037b02c4db638 — reliable collection, data quality (Week 8)
- `cp3` 82b5f29b6e986fb3b32900f9dc4c0d8d1fed326d — statistical analysis (Week 9)
- `cp4` 7341057c4e00410c5504c1ff9962b1c582057186 — integrated end-to-end system (Week 10)

`docs/evidence-register.md` holds the register, and `docs/checkpoints/CP1–CP4.md` the per-checkpoint
records. Collection is running twice daily inside the approved window: 32 assessed runs so far,
2,571 distinct competitor products and 45,852 price observations, every one traceable to the HTTP
request, run and commit that produced it.

I have five questions, each with what I intend to do so you can simply confirm or correct me.

**1. Checkpoint records.** No checkpoint form appeared on the LMS, and your email of 26 October
confirmed that the assessment has one final submission in Week 12 with checkpoint records submitted
alongside the report. I have followed that: each checkpoint is a tagged commit with its own record
in the repository. Could you confirm that nothing further was required for Weeks 7–10? I ask only
because the brief states that GitHub activity without the checkpoint form is not a submission, and I
would rather resolve it now than discover a gap after the deadline.

**2. A success criterion I will miss.** My approved objective O1 was that at least 95% of scheduled
runs reach every operator group. The actual figure is 21 of 32 runs (66%). The 11 incomplete runs
all fall in the first week: `robots.txt` requests to the largest site timed out, and that site then
redesigned its theme on 13 November so pages returned HTTP 200 while the parser found nothing. Both
causes are fixed — the parser now reads both layouts, and a per-group freshness check fails on the
first run in which any source goes quiet — and every run since 15 November has reached all four
groups, 19 consecutively. Even if every remaining run is clean, the final rate will be about 80%.
I intend to report the criterion as **missed**, with the causes, the fixes and the effect on the
findings. Is that the handling you expect, or would you prefer anything else recorded?

**3. Secret's own prices.** As approved (my 29 October addendum), Secret's prices are reference data
from a one-off export the owner produces himself, which I will import after the window closes on
6 December. Until then every Secret comparison in my analysis reports "insufficient evidence" rather
than an estimate, and the analysis compares the four competitors with each other. Two questions: if
the owner does not provide the export in time, is reporting that comparison as insufficient evidence
acceptable, or would you prefer a different fallback? And is a written consent statement from the
owner by message sufficient, or do you require a signed note?

**4. One table from my proposal that I did not build.** My approved analysis plan (v2.0) compares
prices **by category**, because Secret's posts rarely state flower type and never state stem count.
A per-product matching table (`product_matches`) would therefore hold nothing the analysis uses, so
I did not build it, and I record the reason in `docs/decisions/ADR-009`. I take this as covered by
your approval of the revised plan rather than as a departure from scope — could you confirm?

**5. Secret's operational tables.** My proposal promised an operational core (clients, orders,
payments, staff). Secret takes orders by phone and Telegram and keeps no digital record, so these
tables exist with **synthetic fixtures only**. Every row carries an `is_synthetic` flag that the
database enforces, none of it reaches the analysis, and the dashboard shows the synthetic count
beside every total. Is that acceptable as database evidence, given it is declared throughout?

Two smaller points, if you have a view: my report currently runs to about 3,800 words against the
3,500 guidance, and I was not sure whether you expect an entity-relationship diagram in the
appendices, since the brief asks for entities, keys and constraints to be explained rather than
drawn.

Thank you for your time.

Best regards,
Dilmurod Tolipov
Student ID 50000161
