# Dependency Graph Collection for GG24 Deep Funding

This project maps the software dependencies behind 98 open source projects from the GG24 Deep Funding round.

## What We Did

### Collected the 98 Seed Projects  
We fetched the seed repositories from the [GG24 Deep Funding Market Weights](https://raw.githubusercontent.com/davidgasquez/gg24-deepfunding-market-weights/refs/heads/main/data/phase_2/weights/elo.csv) repository, which contains 98 repositories ranked by ELO score.

### Gathered Their Dependencies  
Different projects use different languages and tools, so we used a flexible, three-step process:

1. **Fast GitHub API lookup** – worked for most projects.  
2. **More detailed GitHub API lookup** – used when the simple method failed and we needed to parse the manifest files manually.  
3. **Local analysis** – for the small number of projects too large or complex for the GitHub API (eg, monorepos and projects with many manifest files).  
   This involved downloading the project and reading files like `package.json`, `Cargo.toml`, `go.mod`, etc.

Using these steps, we were able to fully process all **98** seed repositories.

We did our best to filter out transitive dependencies, either using the relationship field from the GitHub API or by applying our own heuristics when parsing the manifest files manually.

We also ignore GitHub Actions.

### Diffed Against Existing Data  
Some dependency information already existed in the [gg24 subdirectory](../gg24/).

We combined both sources using a simple rule:

- If there was existing data, we kept it as is.  
- If there was no existing data, we added our collected data.  

This ensured we didn’t overwrite anyone’s past work while still improving incomplete entries.

### Looked Up Package Owners

We used pyoso to look up the package owners for each package.

## How the Data Is Organized

The final output is a JSON file where each project links to the repositories it depends on, for example:

```json
{
  "https://github.com/owner/repo": [
    "https://github.com/dependency1/repo1",
    "https://github.com/dependency2/repo2"
  ]
}
```