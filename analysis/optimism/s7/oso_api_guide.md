# Open Source Observer GraphQL API Guide for TypeScript

This guide demonstrates how to access the Open Source Observer GraphQL API using GraphQL queries from a TypeScript environment. It explains how to replicate various data requests originally implemented with pyoso in Python. Note the following:

- **Naming Convention:** All table names and field names are in camelCase with an "oso" prefix (e.g., `oso_projectsV1` instead of snake_case).
- **No Joins:** The GraphQL API does not support SQL-style joins. To combine data from multiple tables, you must issue separate queries and merge the results in your application.
- **Endpoint:** All queries are sent to the API endpoint described below.

---

## API Endpoint

Send your GraphQL queries to:

```bash
curl --request POST \
  --header 'Content-Type: application/json' \
  --url 'https://www.opensource.observer/api/v1/graphql' \
  --data '{"query": "query { __typename }"}'
```

---

## GraphQL Queries

Below are several example queries. Replace placeholder values (such as project IDs or metric IDs) with actual data from your dataset.

### 1. Get a Project by Name (OP Atlas)

Retrieve a project using its OP Atlas ID:

```graphql
query GetAtlasProject {
  oso_projectsV1(limit: 1, where: { projectName: "0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd" }) {
    projectId
    projectName
    description
    displayName
    projectNamespace
    projectSource
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_projectsV1": [
      {
        "projectId": "5/9fRbVoDF7pHwBdiMbNUbKhidEt/12Ojt9f8cWoZnQ=",
        "projectName": "0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
        "description": "The central trading & liquidity marketplace on...",
        "displayName": "Velodrome Finance",
        "projectNamespace": "",
        "projectSource": "OP_ATLAS"
      }
    ]
  }
}
```

---

### 2. Get Artifacts for a Project

Retrieve artifacts associated with a project:

```graphql
query GetAtlasArtifacts {
  oso_artifactsByProjectV1(where: { projectName: "0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd" }) {
    artifactId
    artifactName
    artifactSource
    # Add additional fields as needed
  }
}
```

---

### 3. Get Timeseries Metrics for an OP Atlas-Sourced Project

Fetch timeseries metrics for a specific project using its project ID:

```graphql
query GetOpAtlasMetrics {
  oso_timeseriesMetricsByProjectV0(where: { projectId: "5/9fRbVoDF7pHwBdiMbNUbKhidEt/12Ojt9f8cWoZnQ=" }) {
    metricId
    sampleDate
    amount
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_timeseriesMetricsByProjectV0": [
      {
        "metricId": "7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4=",
        "sampleDate": "2025-02-28",
        "amount": 106
      },
      {
        "metricId": "UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs=",
        "sampleDate": "2025-02-28",
        "amount": 11813776464500
      }
    ]
  }
}
```

---

### 4. Get an OSO Project by Human-Readable Name

Retrieve a project using a human-readable OSO name (e.g., "velodrome"):

```graphql
query GetOsoProject {
  oso_projectsV1(limit: 1, where: { projectName: "velodrome" }) {
    projectId
    projectName
    description
    displayName
    projectNamespace
    projectSource
  }
}
```

---

### 5. Look Up Metric IDs

Query to list available metrics and their IDs:

```graphql
query GetMetricIds {
  oso_metricsV0 {
    metricId
    metricName
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_metricsV0": [
      {
        "metricId": "7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4=",
        "metricName": "OPTIMISM_transactions_over_30_day_window"
      },
      {
        "metricId": "UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs=",
        "metricName": "OPTIMISM_gas_fees_over_30_day_window"
      },
      {
        "metricId": "+5rLhj0Pg2P/g3AVc2Y7Rvqb90r8SMl+wW3gxFUlejE=",
        "metricName": "OPTIMISM_active_addresses_aggregation_over_30_day_window"
      }
    ]
  }
}
```

---

### 6. Get Timeseries Metrics for a Specific Date

Query timeseries metrics for a project on a specific date:

```graphql
query GetTimeseriesMetrics {
  oso_timeseriesMetricsByProjectV0(where: { 
    projectId: "H1DdvseIeFYJUwYwfSNvsXvbgxfwasspZw2MT3Apkfg=", 
    sampleDate: "2025-02-28" 
  }) {
    metricId
    sampleDate
    amount
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_timeseriesMetricsByProjectV0": [
      {
        "metricId": "7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4=",
        "sampleDate": "2025-02-28",
        "amount": 106
      },
      {
        "metricId": "UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs=",
        "sampleDate": "2025-02-28",
        "amount": 11813776464500
      }
    ]
  }
}
```

---

### 7. Get Transaction Metrics Over a Date Range

Fetch transaction metrics for a project within a specified date range:

```graphql
query GetTransactionMetrics {
  oso_timeseriesMetricsByProjectV0(
    where: {
      projectId: { _eq: "H1DdvseIeFYJUwYwfSNvsXvbgxfwasspZw2MT3Apkfg=" },
      sampleDate: { _gte: "2025-01-01", _lte: "2025-02-28" },
      metricId: { _in: ["7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4="] }
    }
  ) {
    metricId
    sampleDate
    amount
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_timeseriesMetricsByProjectV0": [
      {
        "metricId": "7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4=",
        "sampleDate": "2025-01-01",
        "amount": 1623
      },
      {
        "metricId": "7PEA33NdLXZ97ichlOnybqpjNAFz84fYFp+Gm7OgGw4=",
        "sampleDate": "2025-02-28",
        "amount": 106
      }
    ]
  }
}
```

---

### 8. Get Active Addresses Metrics Over a Date Range

Retrieve active addresses metrics for a project over a specific date range:

```graphql
query GetActiveAddressesMetrics {
  oso_timeseriesMetricsByProjectV0(
    where: {
      projectId: { _eq: "H1DdvseIeFYJUwYwfSNvsXvbgxfwasspZw2MT3Apkfg=" },
      sampleDate: { _gte: "2025-01-01", _lte: "2025-02-28" },
      metricId: { _in: ["+5rLhj0Pg2P/g3AVc2Y7Rvqb90r8SMl+wW3gxFUlejE="] }
    }
  ) {
    metricId
    sampleDate
    amount
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_timeseriesMetricsByProjectV0": [
      {
        "metricId": "+5rLhj0Pg2P/g3AVc2Y7Rvqb90r8SMl+wW3gxFUlejE=",
        "sampleDate": "2025-01-01",
        "amount": 1163
      },
      {
        "metricId": "+5rLhj0Pg2P/g3AVc2Y7Rvqb90r8SMl+wW3gxFUlejE=",
        "sampleDate": "2025-02-28",
        "amount": 61
      }
    ]
  }
}
```

---

### 9. Get Gas Fees Metrics Over a Date Range

Fetch gas fees metrics for a project within a specified date range:

```graphql
query GetGasFeesMetrics {
  oso_timeseriesMetricsByProjectV0(
    where: {
      projectId: { _eq: "H1DdvseIeFYJUwYwfSNvsXvbgxfwasspZw2MT3Apkfg=" },
      sampleDate: { _gte: "2025-01-01", _lte: "2025-02-28" },
      metricId: { _in: ["UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs="] }
    }
  ) {
    metricId
    sampleDate
    amount
  }
}
```

_Example response:_

```json
{
  "data": {
    "oso_timeseriesMetricsByProjectV0": [
      {
        "metricId": "UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs=",
        "sampleDate": "2025-01-01",
        "amount": 288883170455473
      },
      {
        "metricId": "UtO9UyVu2lYYPzCjiBlIvXGxY+QNVyi+jPHYzVtBoEs=",
        "sampleDate": "2025-02-28",
        "amount": 11813776464500
      }
    ]
  }
}
```

---

### 10. Get Project Dependencies

Retrieve project dependencies from the SBOMs table:

```graphql
query GetDependencies {
  oso_sbomsV0(where: { fromProjectId: { _eq: "H1DdvseIeFYJUwYwfSNvsXvbgxfwasspZw2MT3Apkfg=" } }) {
    fromProjectId
    # Add other available fields as needed
  }
}
```

---

## Usage Notes

- **No Joins:** Since the GraphQL API does not support joins, any data combination (such as linking metrics to their names) must be performed by issuing separate queries and combining the results in your application.
- **Replace Placeholders:** Ensure that you replace placeholder values (e.g., project IDs, metric IDs) with actual values from your dataset.
- **Naming Conventions:** All queries and field names follow the camelCase naming convention with an "oso" prefix.
