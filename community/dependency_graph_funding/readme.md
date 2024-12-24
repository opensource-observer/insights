# Dependency Graph Funding

## Project Overview

This project involves analyzing a depth-2 directed graph of dependencies and using it to allocate funding. The graph consists of nodes representing repositories (on GitHub and various package managers) that are one or two hops away from Ethereum.

For example:
```json
{
   "relation": "GO",
   "weight": 0.1,
   "source": "https://github.com/prysmaticlabs/prysm",
   "target": "https://github.com/multiformats/go-multihash"
}
```

The `source` in the graph is the **dependent** node and the `target` is the **dependency** node. By weighting the edges of the graph, we aim to signal the most important dependencies and allocate funding proportionally to them.

Your job is to submit a list of weights for the edges, where the weight of an edge `source` (dependent) -> `target` (dependency) represents the portion of the credit for `source` (dependent) that belongs to `target` (dependency). The weights coming out of a `source` node into its `target` nodes should sum to less than one; the remainder represents the portion of credit that rests with the `source` node itself.

You can mine GitHub, dependency, and blockchain data for free from [OSO's BigQuery](https://docs.opensource.observer/docs/integrate/) or connect to other data sources.

## Getting Started

1. Explore the dependency data at `./data/unweighted_graph.json`. In this version, every edge has equal weight. You can also use `./data/unweighted_graph.csv` if you prefer (or you want to pass more information to your graph).
2. Try running the `Example_WeightedGraph.ipynb` notebook to see how we might construct a weighted graph. This version uses a very naive approach based on repository stars to weight the edges. The result is exported to `./data/example_weighted_graph.json`.
3. Experiment! You can access more public datasets from [OSO's BigQuery](https://docs.opensource.observer/docs/integrate/) and use [Vertex AI](https://cloud.google.com/vertex-ai/docs/training/overview) to train your own model. Or you can take things in a completely different direction!
4. We'll be posting more instructions on how solutions will be evaluated soon.

## How It Works

The initial graph is seeded with the primary repos of the top consensus and execution layer projects (according to https://clientdiversity.org). We also include a set of related infrastructure projects as seed nodes.

The full list of seed nodes is: 

- `prysmaticlabs/prysm`, `sigp/lighthouse`, `consensys/teku`, `status-im/nimbus-eth2`, `chainsafe/lodestar`, `grandinetech/grandine`
- `ethereum/go-ethereum`, `nethermindeth/nethermind`, `hyperledger/besu`, `erigontech/erigon`, `paradigmxyz/reth`
- `ethereum/solidity`, `ethereum/remix-project`, `vyperlang/vyper`, `ethereum/web3.py`, `ethereum/py-evm`, `eth-infinitism/account-abstraction`, `safe-global/safe-smart-account`, `a16z/helios`, `web3/web3.js`, `ethereumjs/ethereumjs-monorepo`

Next, we pull the Software Bill of Materials (SBOM) for each of the above repositories and identify all packages in Go, Rust, JavaScript, and Python. 

This gives us a list of over 6,000 packages:

- JavaScript: 4750 (hosted on npm)
- Rust: 1076 (hosted on crates.io)
- Go: 416 (hosted on GitHub)
- Python: 137 (hosted on PyPi)

Finally, we try to map each package to an open source repository and build a dependency graph. In total, we are left with 3,990 GitHub repositories and over 10,000 edges in the graph.

The notebook used to create the initial graph is `DataPrep.ipynb`. Let us know if you find any issues with the data or the graph construction. Feel free to fork it and create your own graph!

## Ideas for Weighting the Graph

In `Example_WeightedGraph.ipynb`, we show some examples of how you can join the graph on other OSO datasets and start weighting the graph. We include a simple (and probably very bad) method for weighting the graph based on the harmonic mean of the repository stars between two nodes.

We've also included a parquet file with >1M rows of GitHub activity data from 2020 to 2024 for all relevant repositories. 

This includes:

| Data Type | Count |
|------------|-------|
| Git Users | 286,740 |
| GitHub Repos | 3,990 |
| Code Commits | 533,503 |
| Issue Comments | 861,824 |
| Repository Forks | 199,195 |
| Issues Opened | 218,345 |
| Issues Closed | 126,357 |
| Issues Reopened | 4,474 |
| PRs Opened | 386,929 |
| PRs Closed | 381,165 |
| PRs Merged | 313,453 |
| PRs Reopened | 3,319 |
| PR Review Comments | 531,096 |
| Releases Published | 28,597 |
| Stars | 445,527 |

## Additional Resources
- Get more data (free): [OSO Documentation](https://docs.opensource.observer/docs/integrate/)
- Ask questions: [OSO Discord](https://www.opensource.observer/discord)
- Report issues: Open an issue in this repository
