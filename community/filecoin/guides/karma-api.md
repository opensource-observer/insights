# Fetching Filecoin data from Karma GAP API

The [Karma GAP](https://gap.karmahq.xyz) (Grantee Accountability Protocol) tracks milestones and grant progress for Filecoin ProPGF recipients. Data is stored as EAS attestations on Base and indexed by the Karma API.

**Base URL:** `https://gapapi.karmahq.xyz`

**Auth:** None required for read endpoints. Rate limit is ~200 requests per window (~60s).

## When to use the API vs the OSO warehouse

OSO already ingests Karma data on a scheduled basis into `filecoin.karma_milestones.*` and `filecoin.karma.*` (see [Relationship to OSO warehouse data](#relationship-to-oso-warehouse-data) below). For most analysis — joining milestones with developer activity, onchain metrics, or funding data — use the warehouse tables.

Use the API directly when you need **real-time or near-real-time data** that can't wait for the next scheduled ingestion run, eg:
- Checking whether a milestone was just submitted or verified
- Building a live monitoring dashboard
- Triggering alerts on status changes
- Ad-hoc checks during grant review calls

---

## Quick start

```bash
# No API key needed
curl "https://gapapi.karmahq.xyz/communities/filecoin/grants?pageLimit=100" | python -m json.tool
```

Or use the companion script:

```bash
uv run fetch_karma.py                    # fetch all Filecoin grants + milestones
uv run fetch_karma.py --project lighthouse  # single project
uv run fetch_karma.py --output karma.csv    # save to CSV
```

---

## Key endpoints

All endpoints return JSON. Pagination via `?page=0&pageLimit=100`.

### Communities

| Endpoint | Description |
|---|---|
| `GET /communities` | List all communities. Filter: `?filter[name]=filecoin` |
| `GET /communities/filecoin` | Filecoin community metadata |
| `GET /communities/filecoin/grants` | All Filecoin grants with milestones (the main endpoint) |

### Projects

| Endpoint | Description |
|---|---|
| `GET /projects` | List projects. Filter: `?filter[title]=<name>` or `?q=<search>` |
| `GET /projects/{uidOrSlug}` | Get project by UID or slug |
| `GET /projects/{uidOrSlug}/grants` | Grants for a project |
| `GET /projects/{uidOrSlug}/milestones` | Milestones for a project |

### Grants

| Endpoint | Description |
|---|---|
| `GET /grants/{uid}` | Get grant by UID |
| `GET /grants/external-id/{id}` | Get grant by external ID |

### Grantees (by ETH address)

| Endpoint | Description |
|---|---|
| `GET /grantees/{address}/grants` | Grants for a grantee |
| `GET /grantees/{address}/projects` | Projects for a grantee |
| `GET /grantees/{address}/communities` | Communities. `?withGrants=true` |

### Search

| Endpoint | Description |
|---|---|
| `GET /search?q=<query>` | Search across projects and communities |

---

## Data structures

### Grant object

```json
{
  "uid": "0x...",
  "chainID": 8453,
  "projectUID": "0x...",
  "communityUID": "0x...",
  "programId": "1013_42161",
  "details": {
    "title": "Grant title",
    "amount": "520000",
    "currency": "USD",
    "description": "Full grant description",
    "proposalURL": "https://fil-propgf.questbook.app/...",
    "payoutAddress": "0x...",
    "startDate": "2024-01-15T00:00:00.000Z",
    "receivedDate": "2024-02-01T00:00:00.000Z",
    "isCompleted": false
  },
  "milestones": [...],
  "updates": [...],
  "project": { ... },
  "categories": ["Infrastructure"],
  "regions": [],
  "milestone_count": 5
}
```

### Milestone object

```json
{
  "uid": "0x...",
  "title": "Milestone 1: Launch beta",
  "description": "Deploy beta version with core features",
  "dueDate": "2024-06-01T00:00:00.000Z",
  "currentStatus": "completed",
  "statusUpdatedAt": "2024-05-28T12:00:00.000Z",
  "statusHistory": [
    {
      "status": "completed",
      "updatedAt": "2024-05-28T12:00:00.000Z",
      "updatedBy": "0x...",
      "statusReason": "Beta launched at app.example.com"
    }
  ],
  "verified": [
    {
      "uid": "0x...",
      "attester": "0x...",
      "reason": "Verified beta is live",
      "createdAt": "2024-06-02T10:00:00.000Z"
    }
  ],
  "completed": {
    "uid": "0x...",
    "createdAt": "2024-05-28T12:00:00.000Z",
    "reason": "Beta deployed",
    "proofOfWork": "https://app.example.com",
    "attester": "0x..."
  }
}
```

### Project object

```json
{
  "uid": "0x...",
  "chainID": 8453,
  "owner": "0x...",
  "details": {
    "data": {
      "title": "Project Name",
      "description": "Project description",
      "problem": "What problem it solves",
      "solution": "How it solves it",
      "imageURL": "https://...",
      "links": [{"url": "https://github.com/...", "type": "github"}],
      "tags": ["defi", "storage"],
      "slug": "project-name"
    }
  },
  "members": [...],
  "endorsements": [...],
  "milestones": [...],
  "impacts": [...],
  "communities": [...]
}
```

### Milestone status values

| Status | Meaning |
|---|---|
| `pending` | Not yet started |
| `completed` | Submitted by grantee, awaiting verification |
| `verified` | Confirmed by a verifier |
| `approved` | Approved by community admin |
| `rejected` | Rejected by verifier |

---

## Filecoin-specific notes

- The Filecoin community slug is `filecoin` (there's also `filecoin-optimism` with 0 grants currently)
- As of May 2026, there are ~33 grants across three programs:
  - **ProPGF Batch 1** (`programId: 1013_42161`, `1013_10`, `1013`) -- amounts populated (eg 520K, 440K, 1M USD)
  - **ProPGF Batch 2** (`programId: 992`) -- amounts often empty
  - **ProPGF Batch 2 - Pods Track** (`programId: 1039`)
- Batch 1 `proposalURL` fields link to Questbook (`fil-propgf.questbook.app`)
- Grant amounts for Batch 2 may be tracked elsewhere (eg Questbook or internal sheets)

---

## Relationship to OSO warehouse data

Karma data is also ingested into the OSO data warehouse as:

| API source | OSO table |
|---|---|
| Project registry | `filecoin.karma.registry` (~34 projects) |
| Milestones | `filecoin.karma_milestones.milestones` |
| Karma-to-OSO mapping | `filecoin.entities.bridge_karma_to_oso` |

OSO runs scheduled jobs to ingest this data, so the warehouse tables stay reasonably current but will lag the live API by hours to days depending on the refresh cadence. Use the warehouse for analytical queries that join milestones with OSO metrics (developer activity, onchain impact, funding). Use the API for real-time checks where freshness matters.

See `skills.md` in this directory for the warehouse query patterns.

---

## SDK

There's also a TypeScript SDK for programmatic access (including write operations):

```bash
npm install @show-karma/karma-gap-sdk
```

Source: [github.com/show-karma/karma-gap-sdk](https://github.com/show-karma/karma-gap-sdk)

The SDK wraps the REST API and adds EAS attestation write capabilities. For read-only data fetching, the REST API is simpler.
