# Critical Review of the Requirements Analysis

Reviews: [requirements-analysis.md](requirements-analysis.md)
Stance: assume the baseline is wrong somewhere and find where. Each finding names the baseline item (A#, FR#, NFR#) it challenges.

---

## Headline Findings (fix before design)

These are not opinions. They are defects in the baseline that would break the demo or contradict the brief.

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| **H1** | **The seed data is in the past.** The brief's events are on 4 and 6 Aug 2026; today is 14 Oct 2026. FR-06 ("start is in the future") would reject **all six demo scenarios** in the baseline. | Brief "Initial Campus Data" vs FR-06 and the demo table | The live demo fails on the first scenario. |
| **H2** | **A3 contradicts the brief.** We limited events to a single day, 07:00–22:00. The brief lists **hackathons** and says events "vary in duration". Hackathons usually run 24–36 hours overnight. | Brief "Context" | An evaluator scenario such as "book a 24-hour hackathon" is wrongly rejected, which looks like we didn't read the problem. |
| **H3** | **A9 makes emergency maintenance impossible.** We forbade blocks over existing bookings. Brief condition 4 lists maintenance as a real cause of unavailability, and a burst pipe doesn't wait for bookings to clear. | Brief condition 4, problem statement ("temporary unavailability due to maintenance") | The Facilities Manager can't record reality; the system diverges from the real world. |
| **H4** | **A6 (suitability table) is invented and enforced as a hard block.** The brief only says the venue must "satisfy the request" (condition 10). Our type→venue table is a guess. | Brief condition 10 | Valid evaluator scenarios (e.g. "club meeting in Seminar Hall") get rejected for a rule nobody asked for. |
| **H5** | **The baseline is over-scoped for 90 minutes.** It has 22 FRs, 12 NFRs, 12 capabilities and 3 bonus options. The brief explicitly rewards *"a smaller, reliable and well-explained solution"*. | Brief Deliverable 1 | The team builds breadth, the core flow is half-finished, and code is generated that nobody can explain. |
| **H6** | **The state model has an unused `Draft` state** and an "optional" `Completed` state, but no requirement uses either. | State diagram vs FR-05–FR-22 | Unexplained states in the diagram invite evaluator questions we can't answer cleanly. |

**Proposed fixes**

- **H1:** add a configurable **"system now"** (demo clock), defaulting to 1 Aug 2026, so seed data stays meaningful. The alternative, shifting the seed dates, changes the customer's data, which is worse.
- **H2:** allow multi-day events and drop the operating-hours rule. Keep only `end > start` and a sanity cap (e.g. ≤ 7 days).
- **H3:** allow a block over existing bookings, but require the Facilities Manager to confirm a **cascade**: affected Pending and Confirmed items become Cancelled with reason "Venue unavailable: maintenance", and that shows on the requester's view.
- **H4:** make capacity the only hard suitability rule. Make the type rule a **warning shown to the reviewer** (or configurable), not a block at submission.
- **H5:** cut scope as described in Section 4.
- **H6:** remove `Draft`. Model "past" as a derived condition (`end < now`), not a stored state.

---

## 1. Which Assumptions Are Risky?

Rated on **likelihood of being wrong × impact if wrong**.

| Assumption | Risk | Why it's risky | Safer position |
|---|---|---|---|
| **A1** Pending holds the venue | Medium likelihood, **high impact** | It's the best reading of conditions 2 and 6, but it opens a **denial-of-service by request**: one club can hold every venue with speculative requests, and nothing expires them in the prototype. | Keep A1 (the brief implies it) and add a **cap on open Pending requests per requester**, plus lazy expiry at start time. |
| **A2** Back-to-back allowed | Low likelihood, medium impact | Real venues need changeover time. If the customer says "30 min buffer", the overlap function changes. | Implement the overlap check with a `buffer_minutes` parameter defaulting to 0. One line to change. |
| **A3** Single-day, 07:00–22:00 | **High likelihood**, high impact | See H2. | Drop it. |
| **A4** Requester or Reviewer can cancel | Medium, medium | "Appropriate end user" may mean *only* the reviewer or authority, because cancellations affect attendees. A requester cancelling a 500-person event the day before may not be acceptable. | Allow both, but show "cancelled by" and the reason. Ask (Q-C3). |
| **A6** Event type → venue type table | **High**, high | See H4. | Warning, not a block. |
| **A7** No minimum utilisation | Medium, low | A 10-person meeting in the 500-seat auditorium is "valid" but wasteful. This is exactly the "venues selected without considering suitability" complaint in the brief. | Warn when attendance < 25% of capacity. Don't block. |
| **A8** Single-level approval | Medium, low (for the prototype) | Universities almost always have layered approvals. Fine for the prototype, but it must be listed as a limitation. | Keep. Document it. |
| **A9** No block over bookings | **High**, high | See H3. | Cascade-cancel. |
| **A10** No editing | Low, medium | It's consistent with condition 6, but a requester who wants to change the attendance from 80 to 85 must cancel, lose the slot, and race to rebook it. | Keep for the prototype. Mention "amend without losing the hold" as next step. |
| **A11** Auto-expiry of stale Pending | Medium, medium | Needs either a scheduler, which is complex infrastructure the brief forbids, or lazy evaluation. If done wrong, expired requests silently keep holding venues. | Lazy evaluation: treat `Pending AND start ≤ now` as non-holding in every query, and block approval. |
| **A14** Role switcher instead of auth | Low, medium | Anyone can be the Reviewer, so segregation of duties can't actually be enforced. | Accept. Explain the trade-off in the pitch (the brief allows it). |
| **Implicit:** "a request has exactly one venue" | Low, low | Condition 9 excludes split bookings, so this is safe. | Keep. |
| **Implicit:** "first-come, first-served is fair" | Medium, medium | With A1, whoever submits first wins, even if a placement drive is more important than a club social. We never stated this. | State FCFS explicitly as a business rule. Raise priority overrides as U4. |

---

## 2. Business Requirements We Haven't Considered

| # | Missing requirement | Why it matters |
|---|---|---|
| BR1 | **Segregation of duties:** a Reviewer must not approve their own request. | A basic control in any approval workflow. Cheap to enforce, even with a role switcher (compare user IDs). |
| BR2 | **Pre-submission availability lookup.** Condition 3 says a conflict must be *prevented before* submission. Rejecting on Submit meets the letter of it. Showing the venue's booked slots *while the requester fills the form* meets the intent. | It's the difference between "the system said no" and "the system helped me". |
| BR3 | **Venue decommissioning / capacity change.** If a venue is deactivated, or its capacity drops (e.g. fire-safety review), what happens to future bookings that no longer fit? | Same cascade problem as H3. |
| BR4 | **Notifying the affected party** when someone *else* acts on their booking (reviewer cancels it, maintenance cascade). Without this, the requester only finds out by checking. | The brief's own pain point: "limited visibility into request status". This is a natural bonus feature. |
| BR5 | **Organizer contact and accountability:** who is responsible for the event, and how to reach them. | Reviewers need it to decide; facilities need it on the day. |
| BR6 | **Limits on duration and on open requests per user.** | Prevents hoarding (see A1). |
| BR7 | **Reason codes**, not just free text, for rejection and cancellation (capacity, conflict, policy, maintenance, organizer request). | Without them, the analytics bonus (e.g. "why are requests rejected?") is impossible. |
| BR8 | **Visibility rules:** can a requester see *who* holds a conflicting slot, or only that it's taken? | Privacy vs. helping the requester negotiate with another club. |
| BR9 | **Past events are read-only.** No cancelling, approving or blocking in the past. | Otherwise history can be rewritten and utilisation reports become meaningless. |
| BR10 | **Releasing a block early** (renovation finishes ahead of schedule) and **extending** one. | Facilities do this routinely, and it's part of "operational restriction". |
| BR11 | **Audit for blocks**, not just event state changes. FR-22 only covers events. | Who blocked the venue, when, and why. |

---

## 3. Missing Edge Cases

These should each become a test case. ✱ = likely to be asked by evaluators.

**Time and overlap**

| # | Case | Expected behaviour |
|---|---|---|
| E1 ✱ | Exact duplicate interval (10:00–12:00 vs 10:00–12:00) | Conflict |
| E2 ✱ | New interval **fully contains** an existing one (09:00–13:00 vs 10:00–12:00) | Conflict. A naive "start falls inside existing" check misses this. |
| E3 | New interval **inside** an existing one (10:30–11:00) | Conflict |
| E4 ✱ | Adjacent (12:00–13:00 after 10:00–12:00) | Allowed (A2) |
| E5 | Adjacent to a **block** (18:00 start after the Conference Room C renovation ends at 18:00) | Allowed. Same rule as events. |
| E6 | Zero-length (start = end) or end < start | Reject with a specific message |
| E7 | Event crosses midnight (22:00–02:00) | Allowed after the H2 fix. Must not be parsed as "end < start". |
| E8 | Second or minute precision mismatch (`10:00:00` vs `10:00:30`) | Normalise to minutes on input |
| E9 | Mixing timezone-aware and naive datetimes in Python | `TypeError` at runtime. Use naive local time everywhere and document it. |
| E10 | Request in the past, or starting "now" | Reject (against the demo clock, H1) |

**State transitions and concurrency**

| # | Case | Expected behaviour |
|---|---|---|
| E11 ✱ | Approve a request whose start time has already passed | Block with a reason (A11) |
| E12 ✱ | Cancel an event that is **in progress** or already ended | Block past events (BR9). In progress: needs a decision, see Q-C4. |
| E13 | Double-click Approve / Cancel (Streamlit reruns re-trigger actions) | Idempotent. The second action fails a state check, not a duplicate write. |
| E14 | Stale UI: the reviewer rejects a request the requester withdrew a second earlier | Re-read state at action time and refuse with "Request is no longer pending" |
| E15 | Two users submit the same slot at nearly the same moment (two browser tabs) | Check and save in one transaction, or behind one lock, so only one wins |
| E16 | Re-approving a Rejected or Cancelled request | Invalid transition (FR-20) |
| E17 | A rejected request is "resubmitted" with identical data | Allowed as a *new* request (condition 6), if the slot is still free |

**Data and validation**

| # | Case | Expected behaviour |
|---|---|---|
| E18 ✱ | Attendance **exactly equals** capacity (120 in Seminar Hall A) | Allowed (≤) |
| E19 | Attendance 0, negative, non-numeric or decimal | Reject |
| E20 | A block overlaps another block on the same venue | Allow (merging isn't needed) or reject, but decide and document it |
| E21 | Block with end < start, or entirely in the past | Reject |
| E22 | Same requester, same time, **different venues** | Allowed? Possibly a mistake or hoarding. See Q-B5. |
| E23 | Seed data integrity: the seeded confirmed events must pass the same validation as new ones | Run seed data through the validator at start-up |
| E24 | Corrupt or missing JSON or SQLite file on start-up | Re-seed with a warning instead of crashing in the demo |

---

## 4. What Could Make This Project Fail?

Ordered by likelihood × damage *for this hackathon*. The evaluation criteria are listed beside each.

| # | Failure mode | Criterion hit | Mitigation |
|---|---|---|---|
| F1 | **Scope overrun.** The core flow isn't finished at minute 90 because the team built roles, audit, dashboards and a bonus. | Implementation 20% | Hard cut (below). Bonus only after the end-to-end flow works and is committed. |
| F2 | **Demo breaks live.** Past seed dates (H1), a Streamlit rerun double-submits, or the data file is in a dirty state from rehearsal. | Implementation, Communication | Demo clock; a **"Reset demo data"** button; rehearse the scripted scenarios once. |
| F3 | **Evaluator's surprise scenario hits an invented rule** (H2, H4) and the team can't justify it. | Problem Understanding 20% | Only enforce rules traceable to the brief. Everything else is a warning or a documented assumption. |
| F4 | **Validation logic duplicated** between submit, approve and block, and the copies drift apart. | Implementation | One `check_venue_available(venue, start, end, exclude_id=None)` function used everywhere, with unit tests. |
| F5 | **Team members can't explain the AI-generated code.** The brief tests every member individually. | AI Usage 20%, Collaboration 20% | Small modules with one owner each. Each owner writes or reviews the tests for their module. |
| F6 | **Weak git history:** one person commits everything at the end, or merge conflicts eat 20 minutes. | Collaboration 20% | Split by file (domain / storage / UI / tests+docs). Small commits from the first 15 minutes. Everyone pulls often. |
| F7 | **Environment setup burns time.** We already hit missing `pypdf` and `poppler` on this machine; the Streamlit install could do the same. | All | Install and verify `streamlit` and the test runner before minute 0. Pin versions in `requirements.txt`. |
| F8 | **Date/time bugs** (E2, E7, E9) produce wrong conflicts. That's the core business rule. | Implementation | Write the overlap function and its tests *first*. |
| F9 | **Pitch slides left to the last 5 minutes.** | Communication 20% | Fill the Slide 1 content from these docs now. Slide 2 grows as decisions are made. |

**Recommended cut for 90 minutes** (replaces the baseline scope table):

- **Must:** venue list; create request with conflict, block, capacity and time validation; reviewer approve/reject with reason; cancel confirmed; release on reject and cancel; role switcher; reset demo data; overlap unit tests.
- **Then, if on time:** block creation with cascade (H3); withdraw; history log.
- **Bonus (pick one):** in-app notification feed for requesters (BR4). It's the cheapest option and directly answers the brief's "visibility" pain point.
- **Explicitly out:** authentication, suitability-type rules as blocks, analytics, .ics export, multi-level approval, editing.

---

## 5. Additional Questions Before Approving the Design

These come *out of this review* and aren't covered by the 24 in the baseline. ★ = blocks design approval.

**Data and time**
- **Q-A1 ★** The sample data is dated August 2026, which is already past. Should the demo run on a simulated "today" (e.g. 1 Aug 2026), or should we move the sample dates forward?
- **Q-A2 ★** Do hackathons or cultural fests need to run **overnight or across several days**? Is there a maximum event length?
- **Q-A3** Should bookings snap to fixed slots (e.g. 30 minutes), or allow any start time?

**Rules**
- **Q-B1 ★** If urgent maintenance hits a venue with confirmed events, should the system **cancel those events automatically** (and tell the organizers), or refuse the block until someone handles them?
- **Q-B2 ★** Is venue/event-type suitability a **hard rule** (reject) or **guidance** (warn the reviewer)? If hard, can you give us the rules?
- **Q-B3** Is first-come, first-served the fairness rule, or should some event types (placement drives, official functions) take priority?
- **Q-B4** Should we limit how many pending requests one organizer can hold at once?
- **Q-B5** May one organizer book two venues for the same time slot?
- **Q-B6** Should the reviewer be warned about poor fit, e.g. 15 people in a 500-seat auditorium?

**Roles and control**
- **Q-C1** Must the approver be a different person from the requester?
- **Q-C2** Can a requester see *who* has booked a conflicting slot, or only that it's unavailable?
- **Q-C3** Should a requester be able to cancel an approved event themselves, or must a reviewer do it?
- **Q-C4** Can an event that has **already started** be cancelled (e.g. stopped halfway)?

**Acceptance**
- **Q-D1 ★** Which scenarios will you use to judge that the system works? If you plan to give us a surprise scenario, what *kind* of rule will it test?
- **Q-D2** Must data survive an app restart, or is in-memory acceptable for the demo?
- **Q-D3** Which ONE bonus feature would be most valuable to campus users?

---

## Changes to Make to the Baseline Document

| Baseline item | Change |
|---|---|
| FR-06 | "start is in the future **relative to the system clock (configurable for demo)**" |
| A3, A13 | Remove the single-day and operating-hours limits; add a max-duration cap |
| A6, FR-10 | Downgrade from a block to a reviewer warning |
| A9, FR-03 | Replace with a cascade-cancel on block creation |
| A1 | Add a cap on open Pending requests per requester |
| State model | Remove `Draft`; make "past" derived |
| FR-22 | Extend the audit to blocks |
| New FRs | BR1 (segregation of duties), BR2 (availability shown while filling the form), BR9 (past is read-only) |
| Scope table | Replace with the cut in Section 4 |
| Demo scenarios | Valid only with the demo clock set before 4 Aug 2026 |
