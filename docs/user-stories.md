# Campus Event Management System: User Stories

> **Build scope:** the 15-minute MVP and bonus are defined in [mvp.md](mvp.md). This file is the full backlog for next steps.

**Sources:** [requirements-analysis.md](requirements-analysis.md) as revised by [critical-review.md](critical-review.md), [solution-design.md](solution-design.md), [architecture.md](architecture.md).

**Conventions**

- **Priority:** **M** = Must (core demo) · **S** = Should (if time allows) · **C** = Could (bonus / stretch).
- **Size:** S ≈ < 10 min · M ≈ 10–20 min · L ≈ 20+ min (for a pair working with AI assistance).
- **Trace:** brief business condition (BC1–BC10), requirement (FR/NFR), review item (H/BR/E).
- **Acceptance criteria** use Given / When / Then. They assume the **demo clock is set to 1 Aug 2026 09:00** and the seed data from the brief is loaded.

**Personas:** Requester (club lead, faculty, placement cell) · Reviewer (Student Affairs) · Facilities Manager · Admin (demo operator) · Developer (technical enablers).

---

## Epic Overview

| Epic | Goal | Stories | Must count |
|---|---|---|---|
| EP1 Access & Roles | Act as different personas | US-01 – US-02 | 1 |
| EP2 Venue Discovery | See venues and when they are free | US-03 – US-05 | 2 |
| EP3 Event Request & Validation | Submit only valid, conflict-free requests | US-06 – US-16 | 7 |
| EP4 Review & Approval | Turn requests into outcomes | US-17 – US-22 | 3 |
| EP5 Event Lifecycle | Track, withdraw, cancel | US-23 – US-27 | 2 |
| EP6 Venue Availability Management | Record maintenance and renovation | US-28 – US-31 | 0 |
| EP7 Audit & History | Show who did what and when | US-32 – US-33 | 0 |
| EP8 Demo Operations | Run a reliable demo | US-34 – US-36 | 2 |
| EP9 Notifications (bonus) | Learn about changes without checking | US-37 – US-38 | 0 |
| EP10 Technical Enablers | Foundation, quality, documentation | TS-01 – TS-05 | 4 |

---

## EP1: Access & Roles

### US-01: Switch the active user and role · M · S
**As a** demo operator, **I want** to choose which user I'm acting as from the sidebar, **so that** I can show every persona's view without building login.

- **Given** the app is running, **when** I open the sidebar, **then** I see the seeded users with their roles (Requester, Reviewer, Facilities, Admin).
- **Given** I pick a user, **when** any page loads, **then** the current user, role and demo date are always visible.
- **Given** I'm a Requester, **when** I open the Review Queue, **then** I see a "Reviewer role required" message and no Approve/Reject buttons.

*Trace:* A14, NFR-10, BC8

### US-02: Only see actions I'm allowed to perform · S · S
**As a** user, **I want** buttons to appear only when I'm allowed to use them, **so that** I'm not offered actions that will fail.

- **Given** I'm the requester of a Confirmed event, **then** I see **Cancel**; another Requester viewing it does not.
- **Given** I'm a Reviewer, **then** I see **Cancel** on any Confirmed event, and **Approve/Reject** on Pending requests that aren't my own.
- **Given** the UI was bypassed (stale page), **when** an unauthorised action reaches the service, **then** it's refused with "You are not allowed to …". The service is the real gatekeeper.

*Trace:* permissions.py, A4, BR1

---

## EP2: Venue Discovery

### US-03: Browse the venue catalogue · M · S
**As a** requester, **I want** to see every venue with its type and capacity, **so that** I can pick one that fits my event.

- **When** I open Venues & Availability, **then** I see the 5 seeded venues with name, type and capacity (e.g. Seminar Hall A, Seminar Hall, 120).
- Inactive venues are marked and can't be selected in the request form.

*Trace:* FR-01, Initial data

### US-04: View a venue's schedule · M · M
**As a** requester or reviewer, **I want** to see a venue's confirmed events, pending holds and blocks for a date range, **so that** I know when it's free.

- **Given** I select Seminar Hall A and 4 Aug 2026, **then** I see a Confirmed event 10:00–12:00.
- **Given** I select Conference Room C and 4 Aug 2026, **then** I see "Blocked: Renovation 09:00–18:00".
- **Given** I select Innovation Lab and 6 Aug 2026, **then** I see a Confirmed event 14:00–17:00.
- Rejected, Withdrawn and Cancelled items are **not** shown as occupying time.
- Each item is visually labelled by status (Confirmed / Pending / Blocked).

*Trace:* FR-04, BC4, problem statement "visibility"

### US-05: See availability while filling in the request form · S · M
**As a** requester, **I want** the selected venue's bookings for my chosen dates to show beside the form, **so that** I avoid a conflict before I submit.

- **Given** I've chosen a venue and a date, **then** the form shows that venue's occupied intervals for that date.
- **When** I change the venue or date, **then** the list updates.

*Trace:* BC3 (intent), BR2

---

## EP3: Event Request & Validation

### US-06: Submit a valid event request · M · M
**As a** requester, **I want** to submit an event request with its details, **so that** it can be reviewed and confirmed.

- **Given** I enter title "Robotics Expo", type Technical Workshop, Main Auditorium, 10 Aug 2026 10:00–13:00, 300 attendees, **when** I submit, **then** I see "Submitted, pending review", and the request is saved with status **Pending Review**.
- The request appears in **My Requests**, the **Review Queue**, and as a **Pending hold** on the Main Auditorium schedule.
- A history entry "submitted by <user>" is recorded.

*Trace:* BC1, BC5, FR-05, FR-12

### US-07: Prevent a request that overlaps a confirmed event or pending request · M · M
**As a** requester, **I want** the system to stop me submitting a request that clashes with an existing booking, **so that** no venue is double-booked.

- **Given** Seminar Hall A is Confirmed 4 Aug 10:00–12:00, **when** I request 4 Aug 11:00–13:00, **then** submission is refused with "Seminar Hall A already has a confirmed event on 4 Aug 2026, 10:00–12:00", and nothing is saved.
- The same refusal happens when my request **fully contains** the existing one (09:00–13:00), is **inside** it (10:30–11:00), or is **identical** (10:00–12:00).
- **Given** another user's request is **Pending** for Main Auditorium 10 Aug 10:00–13:00, **when** I request 12:00–14:00, **then** it's refused, because pending requests hold the venue.

*Trace:* BC2, BC3, FR-07, A1, E1–E3

### US-08: Allow back-to-back bookings · M · S
**As a** requester, **I want** to book a slot that starts exactly when another ends, **so that** venues are used efficiently.

- **Given** Seminar Hall A is Confirmed 10:00–12:00 on 4 Aug, **when** I request 12:00–13:00, **then** it's accepted.
- **Given** Conference Room C is blocked until 18:00 on 4 Aug, **when** I request 18:00–19:00, **then** it's accepted.

*Trace:* A2, E4, E5

### US-09: Prevent a request during venue unavailability · M · S
**As a** requester, **I want** to be stopped from booking a venue that's under maintenance or renovation, **so that** I don't plan an event in an unusable space.

- **Given** Conference Room C is blocked 4 Aug 09:00–18:00, **when** I request 4 Aug 14:00–15:00, **then** it's refused with "Conference Room C is unavailable (Renovation) on 4 Aug 2026, 09:00–18:00".

*Trace:* BC4, BC10, FR-08

### US-10: Prevent a request that exceeds venue capacity · M · S
**As a** requester, **I want** to be told if my expected attendance won't fit, **so that** I choose an adequate venue.

- **When** I request Innovation Lab for 80 attendees, **then** it's refused with "Expected attendance 80 exceeds Innovation Lab capacity of 60".
- **When** I request Seminar Hall A for exactly 120, **then** it's accepted.

*Trace:* BC10, FR-09, A7, E18

### US-11: Validate the event time window · M · S
**As a** requester, **I want** clear errors for an impossible time window, **so that** I can correct my input.

- End equal to or before start → "End time must be after start time".
- Start before the current (demo) time → "Events cannot be booked in the past".
- Duration over the configured maximum (default 7 days) → "Events cannot be longer than 7 days".
- An overnight event (e.g. 10 Aug 18:00 → 11 Aug 06:00) **is accepted**: multi-day hackathons are valid.
- Times are stored at minute precision.

*Trace:* FR-06, H1, H2, E6–E8, E10

### US-12: Validate required fields and attendance · M · S
**As a** requester, **I want** the form to check mandatory fields and attendance, **so that** incomplete requests aren't sent to reviewers.

- A missing title, event type, venue, organizer or date-time → a field-specific message.
- Attendance of 0, a negative number or a non-integer → "Expected attendance must be a whole number greater than 0".

*Trace:* FR-06, E19

### US-13: See every problem with my request at once · S · S
**As a** requester, **I want** all validation failures listed together, **so that** I can fix them in one go instead of one at a time.

- **Given** my request has attendance above capacity **and** an end before its start, **when** I submit, **then** both messages are shown.

*Trace:* validators collect all violations

### US-14: Be warned about a poor venue fit · C · S
**As a** requester and reviewer, **I want** a warning when the venue type is unusual for the event type, or very oversized, **so that** we're nudged toward suitable venues without being blocked.

- **Given** a Cultural Programme requested in Conference Room C, **then** the request is **accepted** with the warning "Conference Room is not a typical venue for Cultural Programme".
- **Given** 20 attendees in the Main Auditorium (500), **then** I'm warned that attendance is under 25% of capacity.
- The warning is shown to the Reviewer in the queue.

*Trace:* H4, A6, A7, problem statement "suitability"

### US-15: Limit open pending requests per requester · C · S
**As a** reviewer, **I want** each requester limited to a configurable number of open pending requests (default 5), **so that** nobody can hoard venues with speculative requests.

- **Given** I already have 5 Pending requests, **when** I submit a sixth, **then** it's refused with "You have reached the limit of 5 open requests".

*Trace:* A1 risk, BR6

### US-16: Guarantee only one of two simultaneous requests wins · S · M
**As a** requester, **I want** a guarantee that two people submitting the same slot at the same moment can't both succeed, **so that** the system stays trustworthy.

- **Given** two sessions submit overlapping requests for the same venue at the same time, **then** exactly one is saved, and the other gets the normal conflict message.
- Verified by an automated service test.

*Trace:* NFR-01, NFR-02, E15

---

## EP4: Review & Approval

### US-17: View the pending review queue · M · S
**As a** reviewer, **I want** a list of pending requests ordered by start time, **so that** I review the most urgent first.

- Each row shows title, event type, venue, time window, attendance vs capacity, requester, and any warnings.
- Requests whose start time has passed are flagged "Expired: cannot be approved".

*Trace:* FR-14, A11

### US-18: Approve a pending request · M · M
**As a** reviewer, **I want** to approve a pending request, **so that** it becomes a confirmed event.

- **Given** "Robotics Expo" is Pending, **when** I approve it, **then** its status becomes **Confirmed**, recording my name and the time, and it shows as Confirmed on the venue schedule.
- At approval the system **re-checks** availability and that the start is still in the future. If either fails, approval is refused with the reason and the status stays Pending.

*Trace:* BC5, FR-15, E11

### US-19: Reject a pending request with a reason · M · M
**As a** reviewer, **I want** to reject a request with a reason, **so that** the requester knows why and the venue is freed.

- Choosing a reason code (e.g. Policy, Insufficient information, Other) and a comment is **mandatory**.
- **When** I reject, **then** the status becomes **Rejected** (closed), and the reason is visible to the requester.
- **Then** the same slot can be requested **immediately** by another user and is accepted.
- A Rejected request has no Edit or Reopen option.

*Trace:* BC6, FR-16, FR-17, A15, BR7

### US-20: Prevent reviewing my own request · S · S
**As the** university, **I want** reviewers to be unable to approve or reject their own requests, **so that** approvals stay independent.

- **Given** I'm a Reviewer who submitted a request, **then** Approve/Reject aren't shown for it, and the service refuses it if attempted.

*Trace:* BR1

### US-21: Handle stale or repeated review actions safely · S · S
**As a** reviewer, **I want** clear feedback if a request changed before I acted, **so that** I don't create inconsistent states.

- **Given** the requester withdrew a request after my page loaded, **when** I click Approve, **then** I see "This request is no longer pending" and nothing changes.
- Double-clicking Approve leads to exactly one status change and one history entry.
- Approving a Rejected, Withdrawn or Cancelled request is refused.

*Trace:* FR-20, E13, E14, E16

### US-22: Start a new request from a rejected one · C · S
**As a** requester, **I want** to copy a rejected request into a new, pre-filled form, **so that** I can revise it without retyping.

- The original stays **Rejected**; the copy goes through full validation as a **new** request.

*Trace:* BC6, FR-17, E17

---

## EP5: Event Lifecycle

### US-23: Track my requests and events · M · S
**As a** requester, **I want** to see all my requests with their current status and any reason, **so that** I don't have to chase anyone for updates.

- I see title, venue, time, status (Pending / Confirmed / Rejected / Withdrawn / Cancelled) and the rejection or cancellation reason, with who made the decision.
- Filterable by status.

*Trace:* FR-21, problem statement "visibility"

### US-24: Cancel a confirmed event · M · M
**As a** requester (event owner) or reviewer, **I want** to cancel a confirmed event with a reason, **so that** the venue is released for others.

- **Given** the seeded Seminar Hall A event on 4 Aug 10:00–12:00, **when** an authorised user cancels it with a reason, **then** its status becomes **Cancelled**, and it disappears from the venue's occupied times.
- **Then** a new request for Seminar Hall A 4 Aug 11:00–13:00 (previously refused in US-07) is **accepted**.
- The cancelling user and reason are recorded and visible.

*Trace:* BC7, BC8, FR-18, A4

### US-25: Prevent invalid cancellations · S · S
**As the** university, **I want** cancellation limited to upcoming confirmed events, **so that** history can't be rewritten.

- Cancelling an event whose end time has passed → "Past events cannot be cancelled".
- There's no Cancel option on Pending, Rejected, Withdrawn or already Cancelled items.
- *Open:* cancelling an event that's in progress is blocked until the customer decides (Q-C4).

*Trace:* BR9, E12, E16

### US-26: Withdraw my pending request · S · S
**As a** requester, **I want** to withdraw a request I no longer need, **so that** I don't keep a venue on hold for nothing.

- **Given** my request is Pending, **when** I withdraw it, **then** its status becomes **Withdrawn** and the slot is free immediately.
- Only the original requester can withdraw.

*Trace:* A5, FR-19

### US-27: See the full timeline of a request · S · S
**As a** requester or reviewer, **I want** to see every status change for a request, **so that** I understand what happened and when.

- The timeline lists each change: from → to, who, when, and the reason.

*Trace:* FR-22, NFR-09

---

## EP6: Venue Availability Management

### US-28: Block a venue for maintenance or renovation · S · M
**As a** facilities manager, **I want** to mark a venue unavailable for a period with a reason, **so that** nobody can book it while it can't be used.

- **Given** Central Amphitheatre has no bookings on 12 Aug, **when** I block it 08:00–20:00 for Maintenance, **then** the block appears on its schedule.
- **Then** a request for Central Amphitheatre 12 Aug 10:00–11:00 is refused with the block reason.

*Trace:* BC4, FR-02

### US-29: Cancel affected bookings when blocking a venue · S · L
**As a** facilities manager, **I want** to see which bookings an urgent block will affect and confirm their cancellation, **so that** the system reflects reality and organizers learn why.

- **Given** Main Auditorium has a Confirmed event on 10 Aug 10:00–13:00, **when** I preview a block for 10 Aug 09:00–18:00, **then** that event is listed as affected.
- **When** I confirm, **then** the block is created **and** every affected Pending or Confirmed event becomes **Cancelled** with reason "Venue unavailable: Maintenance", as one all-or-nothing operation.
- **When** I don't confirm, **then** nothing changes.
- Affected requesters see the cancellation and its reason in My Requests.

*Trace:* BC4, BC8, H3, NFR-02

### US-30: Validate block input · S · S
**As a** facilities manager, **I want** obviously wrong blocks to be refused, **so that** availability data stays accurate.

- End at or before start → refused. A block entirely in the past → refused.
- An overlap with another block on the same venue is **allowed** (documented decision).

*Trace:* E20, E21

### US-31: Release a block early · C · S
**As a** facilities manager, **I want** to end a block early when work finishes ahead of schedule, **so that** the venue can be booked again sooner.

- **When** I release a block, **then** it no longer appears on the schedule, and requests in that period are accepted.
- The release is recorded in history.

*Trace:* BR10

---

## EP7: Audit & History

### US-32: View the audit log · C · S
**As an** admin, **I want** a chronological log of all state changes for events and blocks, **so that** any outcome can be traced to a person and a time.

- Each entry shows timestamp, actor, entity (event or block), from → to and reason.
- Filterable by venue and by user.

*Trace:* NFR-09, BR11

### US-33: Record history for every change automatically · S · S
**As the** university, **I want** every status change and block action written to history in the same transaction, **so that** the log can never disagree with the data.

- No service operation changes a status without a matching history row (verified by service tests).

*Trace:* FR-22, NFR-02

---

## EP8: Demo Operations

### US-34: Reset demo data · M · S
**As a** demo operator, **I want** one button (and a script) that restores the original seed data, **so that** every rehearsal and the final demo start from the same state.

- **When** I click "Reset demo data" and confirm, **then** all user-created records are removed and the brief's seed data is restored.
- `python scripts/reset_db.py` does the same from the command line.

*Trace:* review F2, NFR-06

### US-35: Set the demo date · M · S
**As a** demo operator, **I want** to set the system's "today", **so that** the August 2026 seed data is in the future and the scenarios work.

- The default demo date is 1 Aug 2026 09:00. It's changeable on the Admin page and shown in the sidebar banner.
- All "past/future" rules use this date.

*Trace:* H1, clock.py

### US-36: Start up reliably · S · S
**As a** demo operator, **I want** the app to create and seed its database on first run, and recover from a missing or corrupt file, **so that** the demo never fails at launch.

- First run with no DB → schema created, seed loaded, app opens.
- Corrupt DB file → it's backed up, the DB is re-seeded, and a warning is shown. The app doesn't crash.
- Seed records are checked by the same validators as user input; invalid seed data fails loudly at start-up.

*Trace:* E23, E24, NFR-06

---

## EP9: Notifications (Bonus)

### US-37: Get notified when someone acts on my request · C · M
**As a** requester, **I want** an in-app notification when my request is approved, rejected or cancelled by someone else, **so that** I learn about it without checking repeatedly.

- The sidebar shows an unread count for the current user.
- Notifications are created for: approval, rejection (with reason), cancellation by a reviewer, and cancellation by a maintenance block.
- No notification is created for my own actions.

*Trace:* BC10, BR4, U11

### US-38: Mark notifications as read · C · S
**As a** requester, **I want** to mark notifications as read, **so that** the unread count reflects only new news.

- Opening the notification list and clicking "Mark all read" sets the count to 0.

---

## EP10: Technical Enablers

### TS-01: Project skeleton and one-command run · M · S
**As a** developer, **I want** the folder structure, pinned requirements and an empty Streamlit app committed first, **so that** the team can work in parallel from minute one.

- `pip install -r requirements.txt` then `streamlit run app.py` opens the app on a clean machine.
- The folder layout matches [architecture.md](architecture.md).

### TS-02: Domain rule unit tests · M · M
**As a** developer, **I want** automated tests for every business rule, **so that** we can change code with confidence and show evaluators our validation.

- Covers overlap cases E1–E8, capacity (including equal to capacity), time rules, every allowed and forbidden state transition, and permissions.
- `pytest` passes locally.

### TS-03: End-to-end service flow tests · M · M
**As a** developer, **I want** tests that run full flows against a temporary database, **so that** the connected lifecycle is proven, not just individual rules.

- Submit → conflict refused; submit → approve → cancel → resubmit accepted; reject releases the slot; block cascade; double approval; simultaneous submissions.

### TS-04: README and documented decisions · M · S
**As an** evaluator, **I want** a README with prerequisites, setup, run steps, assumptions, scope, exclusions, trade-offs, limitations and the pitch, **so that** I can run and judge the solution without the team present.

- Every assumption in the README matches the code's actual behaviour.

### TS-05: Layer dependency discipline · S · S
**As a** developer, **I want** the dependency rules in the architecture enforced in review (pages never import `data/` or `sqlite3`), **so that** business logic stays in one testable place.

- A simple test or review checklist confirms that no page imports `sqlite3` or `cems.data`.

---

## Release Plan (90 minutes)

| Milestone | Time | Stories | Demo-able outcome |
|---|---|---|---|
| **M0 Foundation** | 0–15 min | TS-01, US-01, US-34, US-35 | App opens, user switcher, demo clock, seeded DB |
| **M1 Core rules** | 15–40 min | TS-02, US-03, US-04, US-06 – US-12 | Requests validated: conflicts, blocks, capacity, time |
| **M2 Lifecycle** | 40–60 min | US-17, US-18, US-19, US-23, US-24, TS-03 | **End-to-end:** submit → approve → cancel → slot released |
| **M3 Hardening** | 60–75 min | TS-04, US-02, US-13, US-16, US-20, US-21, US-25, US-26 | README done; edge cases handled; rehearsal |
| **M4 Stretch** | 75–90 min | Pick one: **US-37** (bonus) **or** US-28 + US-29 | Bonus feature shown only if M2 is solid |

Everything not in M0–M4 is listed in the README as a deliberate exclusion or next step.

---

## Traceability: Brief Business Conditions → Stories

| Condition | Stories |
|---|---|
| 1. Start, end, venue | US-06, US-11 |
| 2. No overlapping active requests or confirmed events | US-07, US-08, US-16 |
| 3. Conflict prevented before submission | US-05, US-07 |
| 4. Venue unavailable (maintenance etc.) | US-04, US-09, US-28, US-29 |
| 5. Review before confirmation | US-17, US-18 |
| 6. Reject closes and releases; revision = new request | US-19, US-22 |
| 7. Appropriate user can cancel | US-02, US-24 |
| 8. Cancelling releases the venue | US-24, US-29 |
| 9. No partial/split bookings or suggestions | Excluded by design (no story) |
| 10. Unsatisfiable request stopped with clear reason | US-09, US-10, US-11, US-12, US-13 |

---

## Definition of Ready / Done

**Ready:** the story has acceptance criteria, a priority, a trace to a requirement, and an owner.

**Done:**
1. The acceptance criteria pass manually in the running app.
2. The business rule has an automated test (domain or service level).
3. No business logic in `pages/`; layer rules respected.
4. Committed to `main` with a message that names the story ID (e.g. `US-07: block overlapping requests`).
5. Any new assumption is added to the README.
