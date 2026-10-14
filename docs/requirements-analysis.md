# Campus Event Management System: Requirements Analysis

Source: *Campus Event Management System.pdf* (IIIT Hackathon Challenge brief).
Purpose: the team's shared understanding of the problem before design and build. This feeds Slide 1 of the consulting pitch and the "assumptions" section of the README.

---

## 0. Problem Summary and Stakeholders

**Problem.** Events are coordinated through messages, spreadsheets and informal communication. That leads to double-booked venues, venues picked without checking capacity or fit, no visibility into request status, slow reviews, venues left blocked after cancellations, and maintenance closures that nobody tracks.

**Goal.** One place where an event goes from *request → review → confirmed/rejected → (optionally) cancelled*, and where the venue is never committed twice.

| Stakeholder / Persona | Primary need |
|---|---|
| **Event Requester / Organizer** (student club lead, faculty, placement cell) | Find a suitable free venue, submit a request, track its status, cancel if plans change |
| **Event Reviewer / Approver** (Student Affairs office, Dean's office) | See pending requests with enough context to approve or reject quickly, with a reason |
| **Venue / Facilities Manager** | Maintain the venue catalogue (type, capacity), block venues for maintenance or renovation, see utilisation |
| **System Administrator** | Manage users and roles, seed and reset data |
| **Attendees / Campus community** (secondary) | See the calendar of confirmed events |
| **University management** (secondary) | Reports: venue utilisation, request volumes, approval turnaround |

---

## 1. Business Capabilities

Capabilities describe *what the business must be able to do*, independent of how it's built.

| # | Capability | Sub-capabilities | Priority for the 90-minute prototype |
|---|---|---|---|
| BC1 | **Venue Management** | Maintain the venue catalogue (name, type, capacity, facilities); activate/deactivate venues | Must (seeded data; editing is Could) |
| BC2 | **Venue Availability Management** | Block venues for maintenance, renovation or operational restrictions; release blocks; view the availability timeline | Must |
| BC3 | **Event Request Management** | Capture the request (title, type, date-time window, venue, expected attendance, organizer); validate; submit; withdraw | Must |
| BC4 | **Conflict & Suitability Validation** | Detect time overlaps with active requests, confirmed events and blocks; check capacity and venue-type fit; explain why a request fails | Must |
| BC5 | **Event Review & Approval** | Review queue; approve → confirmed event; reject with reason → closed | Must |
| BC6 | **Event Lifecycle Management** | Cancel confirmed events; release the venue commitment; keep state history | Must |
| BC7 | **Status Tracking & Visibility** | Requester view of "my requests"; reviewer queue; venue calendar | Must (basic) |
| BC8 | **Role-Based Access** | Different views and actions per persona | Should (role switcher, no real auth) |
| BC9 | **Audit & History** | Who did what and when (submit, approve, reject, cancel, block) | Should |
| BC10 | **Notifications** | Tell requesters about approval, rejection or cancellation | Could (bonus) |
| BC11 | **Reporting & Analytics** | Venue utilisation, approval turnaround, request volume by event type | Could (bonus) |
| BC12 | **Calendar Integration** | Export confirmed events (.ics) | Could (bonus) |

---

## 2. Requirements

### 2.1 Functional Requirements

**Venue & availability**

| ID | Requirement | Source |
|---|---|---|
| FR-01 | The system shall keep a venue catalogue with name, type and capacity, seeded with the 5 venues in the brief. | Initial data |
| FR-02 | A Venue Manager shall be able to create an unavailability block (maintenance / renovation / other) for a venue with a start date-time, end date-time and reason. | BC 4 |
| FR-03 | A block shall not be created over an active request or confirmed event without explicit handling. The system shall show the conflicting items (see Assumption A9). | BC 2, 4 |
| FR-04 | Users shall be able to view a venue's availability for a chosen date: confirmed events, pending requests and blocks. | Problem: visibility |

**Event request & validation**

| ID | Requirement | Source |
|---|---|---|
| FR-05 | A Requester shall be able to create an event request with: title, event type, organizer/department, start date-time, end date-time, venue, expected attendance, optional description. | BC 1 |
| FR-06 | Before submission the system shall validate: end > start; start is in the future; all mandatory fields are present; attendance > 0. | BC 3, 10 |
| FR-07 | Before submission the system shall reject the request if the time window overlaps an **active request (Pending)** or **Confirmed event** on the same venue. | BC 2, 3 |
| FR-08 | Before submission the system shall reject the request if the window overlaps an **unavailability block** on that venue. | BC 4 |
| FR-09 | The system shall reject the request if expected attendance exceeds venue capacity. | BC 10 |
| FR-10 | The system shall reject the request if the venue type isn't suitable for the event type (rule table, see Assumption A6). | BC 10, problem: suitability |
| FR-11 | Every rejection at validation time shall show a clear, specific reason, e.g. *"Seminar Hall A already has a confirmed event 10:00–12:00 on 4 Aug 2026"* or *"Expected 150 attendees exceeds capacity 120"*. | BC 10 |
| FR-12 | A request that passes validation shall be saved with status **Pending Review**, and that holds the venue for the time window. | BC 2, 5 |
| FR-13 | The system shall not suggest alternative venues, or allow partial or split bookings. | BC 9 |

**Review & lifecycle**

| ID | Requirement | Source |
|---|---|---|
| FR-14 | A Reviewer shall see a queue of Pending requests, with venue, time, capacity fit and requester. | BC 5 |
| FR-15 | A Reviewer shall be able to **approve** a Pending request, and it becomes a **Confirmed** event. Validation is re-run at approval time in case of race conditions or a new block. | BC 5 |
| FR-16 | A Reviewer shall be able to **reject** a Pending request with a mandatory reason. The request becomes **Rejected** (closed, terminal) and the venue hold is released straight away. | BC 6 |
| FR-17 | Rejected requests cannot be edited or reopened. Revisions need a new request (optionally pre-filled from the rejected one). | BC 6 |
| FR-18 | An authorised user (the original Requester or a Reviewer/Admin, see A4) shall be able to **cancel** a Confirmed event with a reason. The event becomes **Cancelled** and the venue is released straight away. | BC 7, 8 |
| FR-19 | A Requester shall be able to **withdraw** their own Pending request, which releases the hold (see A5). | Derived |
| FR-20 | Only valid state transitions shall be allowed (e.g. no approving a Cancelled event, no cancelling a Rejected request). | Consistency |
| FR-21 | A Requester shall be able to see all their requests and their current status, with the rejection or cancellation reason. | Problem: visibility |
| FR-22 | The system shall record a history entry (timestamp, actor, from-state, to-state, reason) for every state change. | BC 9 |

**Event state model**

```
             submit (passes validation)
   [Draft] ───────────────────────────► [Pending Review] ──approve──► [Confirmed] ──cancel──► [Cancelled]
                                              │   │
                                       reject │   │ withdraw
                                              ▼   ▼
                                       [Rejected] [Withdrawn]

Venue-holding states: Pending Review, Confirmed
Terminal / releasing states: Rejected, Withdrawn, Cancelled
(Optional) Completed: Confirmed whose end time has passed
```

**Overlap rule.** Two intervals `[s1, e1)` and `[s2, e2)` conflict when `s1 < e2 AND s2 < e1`. Back-to-back events (one ends at 12:00, the next starts at 12:00) are allowed (see A2).

### 2.2 Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | **Data integrity** | No two venue-holding records (Pending, Confirmed, Block) overlap on the same venue at any time. Enforced in one validation service that runs at both submission and approval. |
| NFR-02 | **Consistency** | State changes and venue release happen together (one transaction in SQLite, or a single write of the store). |
| NFR-03 | **Usability** | A non-technical requester can submit a request in under 2 minutes. Error messages are specific and actionable, not generic. |
| NFR-04 | **Performance** | Validation and page loads take under 1 second on the expected local data volume (hundreds of venues, thousands of events). |
| NFR-05 | **Portability / Deployability** | Runs locally with Python 3.x and one install command (`pip install -r requirements.txt`). No cloud, external APIs or paid services. |
| NFR-06 | **Persistence** | Data survives an app restart (SQLite or JSON), with a reset/seed option for demos. |
| NFR-07 | **Maintainability** | Business rules sit in a separate domain/service layer, not in the UI, so they can be tested and explained. |
| NFR-08 | **Testability** | Automated tests cover each business rule: overlap, adjacency, capacity, block, reject releases, cancel releases, invalid transitions. |
| NFR-09 | **Auditability** | Every state change can be traced to an actor and a timestamp. |
| NFR-10 | **Security** (prototype level) | Role-based restriction on actions (role selector). Real authentication is out of scope, and that's documented as a trade-off. |
| NFR-11 | **Time handling** | One campus time zone, and date-times stored in a consistent format (ISO 8601). |
| NFR-12 | **Explainability** | Every team member can explain the code. The solution is kept small and readable rather than broad. |

---

## 3. Assumptions to Clarify with the Customer

These are the working assumptions we'll build on unless the customer says otherwise. Each one goes in the README.

| # | Assumption | Why it matters |
|---|---|---|
| A1 | A **Pending** request holds the venue. Brief rules 2 and 6 imply this ("active event requests", "rejecting must release"). | Decides whether two people can request the same slot at once. |
| A2 | Time intervals are half-open: **back-to-back bookings are allowed** (10:00–12:00 and 12:00–14:00 don't conflict). No buffer or setup time between events. | Core overlap logic. |
| A3 | Events can't be booked in the past. An event must be within a single day and between 07:00 and 22:00 (campus operating hours). | Validation rules. |
| A4 | A Confirmed event can be cancelled by **the original Requester or a Reviewer/Admin**. | Rule 7 says "an appropriate end user". |
| A5 | A Requester can **withdraw** a Pending request. The brief doesn't mention this, but it's needed so venues aren't held needlessly. | Extra state. |
| A6 | Venue suitability is a simple **event type → allowed venue types** table, e.g. Hackathon → Computer Lab / Auditorium; Placement session → Seminar Hall / Auditorium / Conference Room; Cultural programme → Auditorium / Open Venue. | Rule 10, "suitability". |
| A7 | Capacity check: expected attendance ≤ venue capacity. No minimum-utilisation rule (a 20-person meeting in a 500-seat auditorium is allowed). | Rule 10. |
| A8 | **One-level approval** by a single Reviewer role. No multi-level chain (faculty advisor → dean → facilities). | Workflow complexity. |
| A9 | A maintenance block **can't be created over** an existing Pending or Confirmed booking. The Venue Manager has to resolve it first (reject or cancel, with a reason). | Rule 4 vs rules 2 and 8. |
| A10 | Confirmed and Pending events **can't be edited**. To change one, cancel or withdraw it and create a new request (matching rule 6 for rejections). | Simplifies state and conflict handling. |
| A11 | If a Pending request's start time passes without review, it **expires** automatically, or approval is blocked. | Venue release, stale queue. |
| A12 | Seeded "Confirmed" events on Seminar Hall A and Innovation Lab are sample events with placeholder titles and organizers. | Initial data. |
| A13 | One campus, one time zone, no recurring events, no multi-day events. | Scope. |
| A14 | Authentication is replaced by a **role selector**. Users are seeded. | Explicitly optional in the brief. |
| A15 | Rejection and cancellation reasons are mandatory free text. | Visibility, audit. |

---

## 4. Unknowns

Unknowns are gaps where we have **no reasonable default**, or where a wrong guess changes the design. They differ from assumptions, where we've picked a default.

| # | Unknown | Impact if wrong |
|---|---|---|
| U1 | **Who the reviewers are** and whether approval depends on event type (placement cell for placement drives, cultural committee for fests). | Routing logic, role model. |
| U2 | **Review SLA**: how fast must requests be reviewed, and what happens if no decision is made? | Expiry rule, escalation. |
| U3 | **Lead-time rules**: minimum notice (e.g. 48 hours) and maximum advance booking (e.g. 90 days). | Validation. |
| U4 | **Priority / precedence**: can a high-priority event (convocation, placement drive) override an existing booking? | Brief rule 2 says no overlap, but real campuses often need overrides. |
| U5 | **Venue facilities** beyond type and capacity (projector, AC, PCs, sound system) and whether requests need to state them. | Suitability model. |
| U6 | **Outdoor venue rules**: weather contingency and noise or time restrictions for the Central Amphitheatre. | Extra constraints. |
| U7 | **Cost or charging**: are some venues chargeable to external or club organizers? | Out of scope, but would change the workflow. |
| U8 | **Requester eligibility**: can any student request, or only registered club coordinators and faculty? | Access control. |
| U9 | **Data volume and growth**: number of venues, events per semester, concurrent users. | Persistence choice beyond the prototype. |
| U10 | **Integration**: will this eventually connect to the university SSO, timetable system or email? (Excluded for the prototype.) | Future architecture. |
| U11 | **What happens to attendees** when a confirmed event is cancelled: notify them? Is there attendee registration at all? | Scope of the notifications/bonus feature. |
| U12 | **Retention**: how long do we keep rejected and cancelled records, and do they need reporting? | Storage, analytics. |

---

## 5. Questions to Ask the Customer

Grouped by topic and ordered by impact on the build. **Ask ★ questions first.** They change core logic.

**Booking rules & conflicts**
1. ★ Should a **pending** request block the venue for others, or only confirmed events? (A1)
2. ★ Are **back-to-back** events allowed, or do you need a buffer for setup and cleanup? If so, how long? (A2)
3. ★ How should we decide whether a venue is **suitable** for an event? Is capacity enough, or are there event-type rules (e.g. hackathons only in labs)? (A6)
4. Is there a minimum notice period or maximum advance window for booking? (U3)
5. Are there campus operating hours outside which venues can't be booked? Can events span several days? (A3, A13)
6. Can any event ever **override** an existing booking (e.g. convocation, VIP visit)? (U4)

**Review & approval**
7. ★ Who reviews requests? One central office, or does it depend on event type or venue? Is there more than one level of approval? (U1, A8)
8. What should happen to a pending request that isn't reviewed before its start time? (A11, U2)
9. Must the reviewer give a reason for rejection? Should it be visible to the requester? (A15)
10. Should the system re-check conflicts at approval time, and what if a block was added in between? (FR-15)

**Cancellation, withdrawal & changes**
11. ★ Who counts as an "appropriate end user" for cancelling a confirmed event: the organizer, the reviewer, facilities, or all three? (A4)
12. Can a requester withdraw a pending request themselves? (A5)
13. Can a confirmed event be **edited** (time, venue, attendance), or must it be cancelled and re-requested? (A10)
14. Is there a cut-off for cancellation (e.g. not within 2 hours of start)?

**Venue availability**
15. ★ If maintenance is scheduled over an already confirmed event, which takes priority? Who tells the organizer? (A9)
16. Who is allowed to block a venue, and can blocks be open-ended (indefinite renovation)?
17. Besides type and capacity, what venue facilities matter for matching? (U5)

**Users & access**
18. Who can submit requests: any student, club coordinators only, faculty, external parties? (U8)
19. Is authentication expected in the prototype, or is a role switcher acceptable for the demo? (A14)

**Visibility, notifications & reporting**
20. What does each stakeholder need to *see*? E.g. should students see a public calendar of confirmed events?
21. Which notification would be most valuable: status changes for requesters, a new-request alert for reviewers, or cancellation notices for attendees? (Bonus feature, U11)
22. What reports matter to management: venue utilisation, approval turnaround, events by type or department? (BC11)

**Data & scope**
23. Can we add more sample venues, users and events for testing and the demo?
24. For the 90-minute prototype, which single end-to-end flow matters most to you? (Our proposal: *Submit → Conflict rejected → Valid submit → Approve → Cancel → Venue released → Rebook*.)

---

## Recommended Scope for the 90-Minute Prototype

| Must (core demo) | Should | Could (bonus) | Won't (documented exclusions) |
|---|---|---|---|
| Seeded venues and events; create request with all validations (FR-05–FR-12); reviewer approve/reject with reason; cancel confirmed; venue release on reject/cancel; maintenance blocks; clear error messages; my-requests and reviewer queue | Role switcher; withdraw pending; audit history; venue day-view; unit tests for each rule | Venue utilisation dashboard **or** in-app notification feed **or** .ics export | Real authentication; alternative-venue suggestions; partial/split bookings; recurring or multi-day events; email/SMS; cloud deployment; multi-level approval |

**Demo scenarios mapped to the seed data**

1. *Conflict:* request Seminar Hall A, 4 Aug 2026, 11:00–13:00 → blocked: overlaps confirmed 10:00–12:00.
2. *Block:* request Conference Room C, 4 Aug 2026, 14:00–15:00 → blocked: under renovation 09:00–18:00.
3. *Capacity:* request Innovation Lab for 80 attendees → blocked: capacity 60.
4. *Happy path:* request Main Auditorium for 300 attendees → Pending → Approve → Confirmed.
5. *Release:* cancel the Seminar Hall A event → resubmit scenario 1 → now succeeds.
6. *Adjacency:* request Seminar Hall A, 4 Aug 2026, 12:00–13:00 → allowed (back-to-back).
