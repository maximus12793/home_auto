# Maintenance Request Routing Plan

## Bottom line

Do not repurpose Crucix as the core product.

Crucix is an intelligence dashboard and alerting app. It is useful as inspiration for:

- scheduled polling
- event aggregation
- alert delivery
- dashboard updates

It is not a maintenance/work-order/vendor platform.

## Recommended direction

Build a small routing layer around an open-source ticket/work-order system instead of trying to force a marketplace dashboard into a property-maintenance workflow.

Recommended base:

1. Atlas CMMS for work requests, workflows, vendors, locations, and cost tracking
2. A thin custom orchestrator in this repo for intake normalization, contractor routing rules, quote collection, and status sync
3. Optional helpdesk front door if you want tenant email/SMS/chat intake before requests hit CMMS

## Why not Crucix

Crucix is optimized for read-heavy external signal aggregation. Your problem is operational:

- collect tenant issue details
- classify urgency/trade
- request bids or quotes
- choose the contractor
- track scheduling and completion
- measure cost and response time

Those require workflow state, permissions, vendor records, SLAs, attachments, approvals, and audit trails.

## OSS options

### Best fit: Atlas CMMS

Use if you want a maintenance-native system.

Strengths:

- service requests and work orders
- locations/assets
- assignment to teams or service providers
- automation triggers
- maintenance cost reporting

Weakness:

- not a contractor marketplace
- you still need a routing/integration layer

### Good front-door option: Zammad or FreeScout

Use if most requests arrive by email and you want a cleaner intake desk.

Strengths:

- email-based ticket intake
- agent workflow
- API/webhook-friendly

Weakness:

- not maintenance-native
- weaker vendor/cost/work-order semantics than a CMMS

### What I would avoid as the primary core

- OpenProject: good project tracking, weak fit for reactive maintenance intake
- generic CRM/ERP first: too much setup for a narrow maintenance-routing problem

## Marketplace/platform reality

There is no clean "one OSS app that automates bids across Fiverr, Taskrabbit, and Upwork" stack.

The main constraint is platform access:

- Taskrabbit has a partner API, but it appears partner/onboarding based
- Upwork has an official developer platform, but access is controlled and the workflow is oriented around jobs, proposals, contracts, and enterprise/client contexts
- Fiverr does not appear to offer a general public marketplace API for this use case

That means a durable system should not depend on scraping those sites.

## Practical architecture

### Core entities

- Portfolio (owner account; scopes all properties for a single operator)
- Property
- Unit
- Tenant
- Request
- Scope
- Trade
- Priority
- Vendor
- Quote
- Dispatch
- Work order
- Invoice

### Portfolio isolation and CMMS location hierarchy

You operate multiple properties: **every** request, message, quote, notification, and work order must be scoped so nothing leaks across buildings and vendors always see the correct address.

**Orchestrator and API rules**

- Tag every domain object with **`portfolio_id`** (or `owner_account_id`), **`property_id`**, and usually **`unit_id`**. Reads and writes require these scopes; do not accept unscoped lists for landlord dashboards.
- Resolve **property address** (and unit/access notes) from this scope before dispatch or vendor matching—never rely on a single global default (e.g. “nearest plumber”) without a property context.

**CMMS alignment**

- Mirror the same hierarchy in the CMMS: e.g. **site/facility = property**, **area or asset = unit** (and equipment on that unit if you track assets). Create or update work orders only after CMMS location IDs are resolved from `property_id` / `unit_id`.
- If the CMMS uses a flatter model, use a consistent convention (custom fields or location codes) so the orchestrator can still map 1:1 and avoid duplicate or mis-addressed work orders.

**Risks this avoids**

- Cross-property visibility in a shared inbox, wrong crew sent to the wrong address, duplicate tickets for the same issue, and analytics that mix unrelated buildings.

### Intake flow

1. Tenant submits request by form, email, text, or voice transcript
2. Intake service extracts:
   - issue type
   - location
   - urgency
   - photos/video
   - access constraints
3. Rules engine classifies the trade:
   - plumbing
   - electrical
   - handyman
   - HVAC
   - appliance
4. System decides:
   - emergency dispatch now
   - request quotes from preferred vendors
   - route to marketplace fallback
5. Work order is created and tracked through completion

### Request provenance, channels, and correlation IDs

The dashboard must answer **who** opened the issue, **when**, and **via which channel**—not only via a retrofitted audit trail.

**Identity**

- Link each `Request` to a **Tenant** record when known: display name, unit, and contact methods on the request.
- On email/SMS intake, treat identity as **asserted** until verified; prefer matching to an existing tenant on file or lightweight verification where practical to reduce spoofing.

**Channel and timestamps**

- Record **`channel`** on first touch: `form`, `email`, `sms`, `voice`, or `helpdesk` (if a ticket front door is used).
- Persist **`created_at`** on the request at intake. Optionally track **`first_response_at`** and **`completed_at`** for SLA and reporting.

**Correlation ID (single issue key)**

- Assign one stable **issue ID** per maintenance thread (UUID or prefixed id, e.g. `REQ-…`). Use it consistently in:
  - the orchestrator and database
  - CMMS work order description or custom field
  - email subject lines and SMS bodies (`[REQ-…]`) so replies thread correctly
- This reduces duplicate work orders when the same problem is reported through multiple channels.

**Immutable event log**

- Append-only **events** per request: status transitions, owner/vendor/tenant actions, connector syncs. This backs `audit/` and answers “who changed what, when” without overwriting history.

### Routing strategy

Use a three-tier vendor waterfall:

1. Preferred local contractors
2. Secondary bench of low-friction on-demand providers
3. Human review fallback for edge cases

This is usually cheaper and more reliable than sending every job into a broad marketplace.

### Quote strategy

Do not wait for "bids" on every request.

Split requests into two lanes:

- standard jobs with fixed routing and pre-negotiated rates
- exception jobs that need multi-vendor quote collection

Examples:

- clogged sink: fixed-rate dispatch list
- outlet sparking: emergency electrical dispatch
- water damage after leak: manual review plus 2-3 vendor quotes

This reduces cycle time more than adding more marketplaces.

### Canonical lifecycle, CMMS mapping, and tenant coordination

CMMS work-order statuses rarely match how you think about a portfolio (e.g. “bidding,” “research,” “waiting on tenant”). Define a **canonical state in the orchestrator** and map to/from the CMMS (and optional helpdesk) so one screen stays truthful.

**Orchestrator states (landlord-facing)**

| State | Meaning |
| --- | --- |
| `Intake` | Captured; not yet fully classified or routed |
| `Triage` | Urgency/trade known; dispatch path not finalized |
| `Research` | Internal/vendor discovery—scope unclear, need estimates, or vendor capability check before committing |
| `Quoting` | Collecting quotes; use this for “bidding” when multiple vendors are in play |
| `VendorSelected` | Vendor chosen; not yet scheduled on site |
| `Scheduled` | Date/time agreed with tenant and/or vendor |
| `InProgress` | Work underway |
| `Completed` | Verified done (or accepted as done) |
| `Cancelled` | Closed without completion |

Adjust names to taste; keep the set small and documented.

**Mapping to CMMS (and optional helpdesk)**

- Maintain an explicit **mapping table**: orchestrator state ↔ CMMS work-order status (and optional helpdesk state). When the CMMS or a webhook updates a work order, sync back to the orchestrator state.
- **Single source of truth per concern** to avoid drift: e.g. CMMS owns **execution** status on the work order; helpdesk owns **conversation transcript** if used; orchestrator owns **portfolio-facing lifecycle** and merges for display.
- If two systems disagree, the orchestrator should prefer **timestamped facts** (last CMMS update vs last message) and surface conflicts in the UI rather than silently overwriting.

**Tenant coordination and human gates**

- **`AwaitingTenant`** (orthogonal or sub-state): blocked on the tenant—for example scheduling access, uploading photos, confirming permission to enter, or clarifying scope. Use **reason codes** such as `schedule_access`, `more_photos`, `confirm_permission_to_enter`, `clarify_scope`.
- **`blocked_by`**: `tenant` \| `vendor` \| `owner` \| `permit` \| `none`—makes “what are we waiting on?” obvious per property.
- **`next_action`**: short owner-facing hint (enum or string) for what unlocks progress.
- **Routing human review** (ambiguous classification, safety, or policy) is separate—e.g. `NeedsOwnerReview`—distinct from waiting on a tenant for access or info.

## Platform integration strategy

### Tier 1: supported integrations

Build direct integrations only where an official API exists and terms allow automation.

### Tier 2: assisted workflows

For platforms without a usable API:

- generate the job scope automatically
- open a prefilled draft for human submission
- ingest replies back into your system by email/webhook/manual paste

This is much safer than scraping.

### Tier 3: off-platform vendors

For your best contractors, skip marketplaces entirely:

- SMS/email quote requests
- vendor portal link
- simple accept/decline/ETA form

This will likely be the biggest cost saver.

## Suggested MVP

Phase 1:

- tenant intake form
- request classification
- Atlas CMMS as work-order backbone
- vendor directory with trade/zip/service hours
- dispatch rules
- email/SMS notifications

Phase 2:

- quote request workflow
- vendor portal for accept/decline/price/ETA
- cost and response-time analytics
- preferred-vendor scorecards

Phase 3:

- limited Taskrabbit or Upwork integration where permitted
- AI-assisted scope summarization
- automatic suggested vendor ranking based on history

## What I would build in this repo

A small service with these modules:

- `intake/` normalize tenant requests; attach portfolio/property/unit, channel, timestamps, and correlation ID
- `triage/` classify urgency and trade
- `router/` choose dispatch path; enforce portfolio/property scope on all side effects
- `state/` canonical lifecycle, CMMS/helpdesk mapping, `blocked_by` / `AwaitingTenant` reason codes
- `vendors/` manage vendor capabilities and scorecards
- `quotes/` collect and compare quotes
- `connectors/` Atlas CMMS, email, SMS, Taskrabbit, Upwork
- `audit/` append-only event stream and reporting (consumes the same events as lifecycle transitions)

**Implementation in this repo:** the Python package [`maintenance_orchestrator/`](maintenance_orchestrator/) mirrors the layout above (intake, triage, router, state, vendors, quotes, connectors, audit) with portfolio-scoped storage, a FastAPI surface in [`maintenance_orchestrator/api/app.py`](maintenance_orchestrator/api/app.py), and a [`README.md`](README.md) for run/test instructions. Replace the in-memory store and `NoOpCmmsConnector` with real persistence and Atlas CMMS when you integrate.

## Decision

If you want the fastest path with the least reinvention:

- use Atlas CMMS as the system of record
- build a lightweight routing/orchestration service around it
- use marketplaces only as fallback channels, not the center of the system

If you want the lowest operational risk:

- avoid depending on Fiverr as an automated backend
- avoid scraping-based workflows entirely

