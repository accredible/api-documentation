# HDR-6545 — Document Issuer Hierarchy changes on Public API Team Members + Departments

**Ticket:** [HDR-6545](https://accredible.atlassian.net/browse/HDR-6545) — the documentation task, covering
two stories in the [HDR-6012](https://accredible.atlassian.net/browse/HDR-6012) epic:

- [HDR-6013](https://accredible.atlassian.net/browse/HDR-6013) (BE subtask HDR-6097) — Team Members: new fields + key-kind authorization
- [HDR-6014](https://accredible.atlassian.net/browse/HDR-6014) (BE subtask HDR-6098) — Departments: scoped API key enforcement

**Reference PR for structure:** [api-documentation#130](https://github.com/accredible/api-documentation/pull/130)
**Branch:** `feature/HDR-6545/update-api-documentation-team-members-departments`

## Context

The Issuer Hierarchy work adds a set of hierarchy fields to the public `team_members` contract and
replaces user-identity authorization with **API-key-kind** authorization across both Team Members and
Departments. Three backend PRs implement it and are all currently **open**:

- [accredible-credential-api#5277](https://github.com/accredible/accredible-credential-api/pull/5277) — team members create (`POST`) + serializer fields
- [accredible-credential-api#5284](https://github.com/accredible/accredible-credential-api/pull/5284) — team members update (`PUT`)
- [accredible-credential-api#5290](https://github.com/accredible/accredible-credential-api/pull/5290) — departments key-scope enforcement
- team members show/destroy work is on branch `temp-issuer-hierarchy` (not yet PR'd)

`openapi.json` in this repo is the public source of truth for `docs.api.accredible.com`, and it
currently documents none of this. This change brings the four Team Members operations and the five
documented Departments operations in line with the shipped contract, following the same structure as
PR #130 (the `pathways` field): additive schema properties + matching example bodies + updated cURL
samples, plus prose for the authorization rules.

**Merge order:** this docs PR must not merge to `develop`/`master` before #5277, #5284 and #5290 ship,
otherwise the published docs describe behaviour the API doesn't have yet. Call that out in the PR body.

### Authoritative sources for the contract

| Fact | Source (accredible-credential-api) |
|---|---|
| Response fields | `app/serializers/api/v1/public/team_member_serializer.rb` (`hierarchy_permissions`) |
| Accepted request params | `app/controllers/api/v1/organization_permissions_controller.rb:645` (`team_member_params`) |
| `access_level` wire ↔ DB names | `config/initializers/frontend_data_mappings/organization_permissions.rb` |
| Key-kind authorization rules | `app/services/organization_permissions/validations/api_key_authorization.rb`, `api_key_management_eligibility.rb` |
| `PUT` replace semantics | `app/services/organization_permissions/public_api/bulk_updater.rb` |
| `DELETE` scope rules | `app/services/organization_permissions/public_api/bulk_destroyer.rb` |

### Decisions taken

- Document **all six** response fields and **all five** accepted request fields, not just the three
  named in the ticket — integrators see all six on the wire regardless.
- Authorization rules go in **prose only** (operation `description` + field descriptions). No new
  `400`/`404` response objects: the spec documents error responses almost nowhere today (one lone
  `422` on `POST /v2/credentials/bulk_create`), and adding them here would be an inconsistent
  one-off.
- Fix the pre-existing `department_id` → `department` bug in the four response schemas/examples.
- Document the two `PUT` behaviour changes (`email` ignored; omitted departments removed).
- Do **not** mention the `issuer_hierarchy` feature flag — public docs describe the target state.

---

## The contract to document

All fields live inside `department_permissions[].permissions`.

**Response — six new fields** (append after `groups`, matching serializer key order):

| Field | Type | Notes |
|---|---|---|
| `api` | boolean | API key access for the Department |
| `team` | boolean | Can manage other Team Members in the Department |
| `spotlight_directory` | boolean | **Response-only** — not accepted on input |
| `access_level` | string | `organization_admin` \| `department_admin` \| `team_member` \| `developer` |
| `analytics_email` | boolean | Receives scheduled analytics emails for the Department |
| `manage_dept_admins_and_devs` | boolean | Can manage Department Admins and Developers |

**Request — five new fields** (insert after `pathways`, before `groups`): `api`, `team`,
`access_level`, `analytics_email`, `manage_dept_admins_and_devs`. All booleans `default: false`.
`access_level` request enum is only the three assignable values — `team_member` (default),
`department_admin`, `developer` — since `organization_admin` is always rejected. The response enum
carries all four.

**Key-kind rules to state in prose:**

| `access_level` | Account-wide key | Department-specific key |
|---|---|---|
| `organization_admin` | never | never |
| `department_admin` | ✅ any department in the account | ✗ |
| `developer` | ✅ any department in the account | ✗ |
| `team_member` | ✅ | ✅ own department only |

Both `department_admin` and `developer` additionally require a plan that supports them
(`validations/plan_entitlement.rb`).

---

## Changes — all in `openapi.json`

Two path objects, four operations: `/v1/team_members` (`post`, line ~9556) and
`/v1/team_members/{id}` (`get`, `put`, `delete`, line ~9821).

### 1. Response schemas + examples — all four operations

For each of the four `responses.200.content["application/json"]` blocks:

- Append the six response properties to the `permissions` `properties` object, after `groups`.
- Rename `department_id` → `department` in the `properties` object **and** in the `required` array
  (`["department_id", "permissions"]` → `["department", "permissions"]`).
- Add the six fields to the `example` body's `permissions` objects (both departments, all four
  operations), and rename the example key `department_id` → `department`.

Give the two example departments contrasting values so the shape reads clearly — e.g. dept 34 as a
`department_admin` with `manage_dept_admins_and_devs: true`, dept 35 as a plain `team_member` with
everything false.

### 2. Request schemas + examples — `post` and `put`

- Add the five request properties (with `default: false` on the booleans, `enum` +
  `default: "team_member"` on `access_level`) after `pathways` in the
  `requestBody.content["application/json"].schema` → `department_permissions.items.permissions.properties`.
  Request keeps `department_id` — that is correct and unchanged.
- Mirror the new fields into the `requestBody` `example` bodies.

### 3. cURL samples — `post` and `put`

Update the single-line escaped `source` string in `x-code-samples` for both operations so the
payload matches the new request example exactly. `get` and `delete` samples have no body — no change.

### 4. Prose — operation descriptions

- **`post` description** — after the existing sentence, add the key-kind matrix in words: Department
  Admins and Developers require an account-wide API key; a department-specific key may only create
  Team Members in its own department; `organization_admin` cannot be created via the API (use the
  Issuer Dashboard); omitting `access_level` creates a Team Member.
- **`put` description** — add: the payload **replaces** the member's permission set (departments
  present are created or updated, departments omitted are removed); removal by omission requires an
  account-wide key; updating an existing Department Admin or Developer requires an account-wide key;
  Organization Admins cannot be updated via the API.
- **`get` description** (currently `""`) — one sentence: an account-wide key returns the member's
  permissions across the whole account; a department-specific key resolves only Team Members within
  its own department.
- **`delete` description** (currently `""`) — an account-wide key removes the member from every
  department in the account; a department-specific key removes only a Team Member in its own
  department; Organization Admins cannot be removed via the API.

### 5. `put` request schema — the two behaviour changes

- Annotate the existing `email` property: `"Ignored. A TeamMember's email address cannot be changed
  through this endpoint."` (keep the property so integrators currently sending it understand why it
  has no effect, rather than silently dropping it from the docs).
- Extend the `name` description: a blank value leaves the existing name unchanged.
- Extend the `department_permissions` description — currently *"This parameter will override any
  existing permissions, not append to them."* — to state explicitly that a department omitted from
  the array has its permission **removed**, and that removal requires an account-wide API key.

---

---

## Departments (HDR-6014 / BE PR #5290)

No schema changes — this story is authorization only, so the docs change is **prose in each operation's
`description`**, consistent with the "no new error response objects" decision above. Behaviour per
`app/controllers/api/v1/departments_controller.rb`:

| Operation | Account-wide key | Department-specific key |
|---|---|---|
| `POST /v1/departments` | full access | `403` `No Permission to manage Departments.` |
| `GET /v1/departments/{department_id}` | any Department | own only; others `404` `No department found` |
| `PUT /v1/departments/{department_id}` | any Department | own only; others `404` `No department found` |
| `DELETE /v1/departments/{department_id}` | full access | `403` `No Permission to manage Departments.` |
| `POST /v1/departments/search` | all Departments | scoped to its own Department |

Two deliberate deviations, both agreed with the ticket owner:

- **Search.** PR #5290 currently returns `Organization.none` (an empty array) for a department-specific
  key. That contradicts AC-E4-S2-2 ("scoped, not 403") and would silently return zero results to
  existing integrators. The docs describe the **intended** behaviour — scoped to its own Department —
  on the basis that the backend will be corrected. **If #5290 merges as-is, this line is wrong.**
- **`GET /v1/departments`** (index) is affected by the change but has never been documented in
  `openapi.json`. Left undocumented; adding it is separate work.

Note also that the ticket's ACs say other-Department `show`/`update` return `403`; the implementation
returns `404`. The docs follow the implementation.

---

## Documented-intent deviations — backend changes required before this merges

Three places where the docs describe **intended** behaviour that the current code does not implement.
Each was an explicit call by the ticket owner. All three need a backend change, or the docs ship wrong:

| # | Documented | Actual behaviour today | Fix needed |
|---|---|---|---|
| 1 | `POST /v1/departments/search` with a department-specific key returns that key's own Department | Returns `[]` (`Organization.none` in `public_search`) | PR #5290 |
| 2 | `role` for a `department_admin` must be `editor` | `editor`, `credential_issuer` and `viewer` are all accepted — only `corporation_admin` is locked to `editor` in `PermissionLocks#locks_for` | add a `role` lock to `organization_admin_locks` |
| 3 | `api: true` on a `department_admin` is permitted and turns every other permission on | Always `400 directory must be true for organization_admin` — the master switch requires `directory: true`, but `directory` is absent from `team_member_params` and pinned to `false` by `BulkCreator::DEFAULT_PERMISSION_PARAMS` | allow `directory` through the public API, or exempt it from the master switch |

Deviation 3 also means the `api` cell for `department_admin` in the permitted-values table reads
`true or false`; until the backend is fixed, sending `api: true` returns `400`.

---

## Constraints while editing

- **Hand-edit `openapi.json`; do not run `process_openapi.py`.** It rewrites the whole file with
  `json.dump(indent=4)`, which would collapse the hand-formatted inline arrays (`[1, 2, 3]`) and
  produce a diff across all 10,607 lines. `add_curl_examples.py` likewise must not be re-run.
- Match surrounding formatting exactly: 4-space indent, inline `[1, 2, 3]` in the `post` examples,
  expanded multi-line arrays in the `{id}` examples (existing inconsistency — preserve per-block).
- Purely additive on request/response properties. The only rename is `department_id` → `department`
  in **responses**.
- Leave `POST` documented as `200` — the controller renders without an explicit status, so `200` is
  correct despite the ticket's AC text saying `201`.

## Verification

1. **Valid JSON, unchanged elsewhere:**
   ```
   python3 -m json.tool openapi.json > /dev/null && echo OK
   git diff --stat        # expect: openapi.json only
   ```
2. **Every documented permission key matches the serializer.** Extract the `permissions` property
   keys for all four operations and diff against the serializer's key list
   (`designs, emails, credential_attributes, analytics, settings, role, pathways, groups, api, team,
   spotlight_directory, access_level, analytics_email, manage_dept_admins_and_devs`) — a short
   throwaway `python3` script over `openapi.json`.
3. **Schema/example agreement:** confirm each operation's `example` body carries exactly the keys its
   schema declares, and that no response block still contains `department_id`:
   ```
   grep -c '"department_id"' openapi.json   # only request-side occurrences should remain
   ```
4. **Render check:** `python3 -m http.server 8080`, open `http://localhost:8080`, and confirm the four
   Team Members operations show the new fields, descriptions, and cURL samples correctly.
5. **Cross-check against the backend specs** — `spec/requests/api/v1/public_api/team_members_spec.rb`
   (`hierarchy_fields` list, line ~1122) and `spec/serializers/api/v1/public/team_member_serializer_spec.rb`
   (line ~131) are the assertions that pin this contract; the documented field set must match them.

## PR

Follow the PR #130 template: ticket link, a "What does this PR do?" list of the changes, type
`📦 Chore/Documentation`, checklist. Explicitly note in the body:
- the `department_id` → `department` response fix as a drive-by correction of a pre-existing bug,
- the two `PUT` behaviour clarifications,
- that this must not merge before accredible-credential-api#5277 and #5284 ship.
