CATEGORIES = [
    {
        "category": "Execution Clients & Core Protocol",
        "description": "Implementations of the Ethereum execution layer (e.g., Geth, Nethermind) plus low‑level consensus or EVM research repos. Anything that validates blocks or directly extends the core protocol logic belongs here."
    },
    {
        "category": "Scaling & Layer‑2 Frameworks",
        "description": "Rollup SDKs, optimistic & zk proof systems, shared sequencers, data‑availability layers, and tooling that lets teams spin up or operate an L2 or sidechain."
    },
    {
        "category": "Interoperability & Bridges",
        "description": "Cross‑chain bridges, messaging buses, generalized state‑proof frameworks, and liquidity routers focused on moving assets or data between networks."
    },
    {
        "category": "Cryptography & Zero‑Knowledge Primitives",
        "description": "Reusable cryptographic libraries—hash functions, elliptic‑curve math, SNARK/STARK circuits, proof systems, and related tooling not tied to a single application."
    },
    {
        "category": "Oracle Networks & Data Feeds",
        "description": "Push or pull‑based oracle contracts, off‑chain reporters, commit‑reveal schemes, and services that bring real‑world or cross‑chain data onchain."
    },
    {
        "category": "Smart‑Contract Languages & Compilers",
        "description": "Compilers, interpreters, transpilers, language servers, and DSLs that translate high‑level code (Solidity, Vyper, Huff, etc.) into EVM bytecode."
    },
    {
        "category": "Development Frameworks & Tooling",
        "description": "Opinionated toolchains (Hardhat, Foundry, Brownie, DappTools) that scaffold, test, and deploy contracts, including plugin ecosystems and CLIs."
    },
    {
        "category": "Testing & Formal Verification",
        "description": "Unit‑test harnesses, fuzzers, static analyzers, symbolic execution engines, and formal verification suites that surface correctness or security issues pre‑deployment."
    },
    {
        "category": "Deployment & Upgrade Management",
        "description": "Libraries and services that automate contract deployment, versioning, proxy patterns, CREATE2 determinism, and governance‑controlled upgrades."
    },
    {
        "category": "Node Operations & DevOps",
        "description": "Scripts, dashboards, container images, and orchestration tools for running or monitoring full nodes, validators, archival nodes, or RPC endpoints."
    },
    {
        "category": "Data Indexing & Analytics",
        "description": "Subgraph definitions, ETL pipelines, time‑series databases, and API servers that structure onchain data for querying, dashboards, or research."
    },
    {
        "category": "Wallets & Account Abstraction",
        "description": "Key‑management libraries, signature middlewares (EIP‑4337), wallet SDKs, browser extensions, mobile wallets, and transaction‑building helpers."
    },
    {
        "category": "Identity & Credentials",
        "description": "ENS, decentralized identity, verifiable‑credential frameworks, reputation scores, soul‑bound token standards, and onchain attestations."
    },
    {
        "category": "DAO & Governance Systems",
        "description": "Token‐weighted voting modules, off‑chain signaling, delegate dashboards, execution timelocks, proposal simulators, and treasury management tooling."
    },
    {
        "category": "DeFi Protocols & Financial Primitives",
        "description": "Lending markets, DEXes, derivatives, yield optimizers, stablecoins, liquidity bootstrapping, onchain indices, and associated SDKs."
    },
    {
        "category": "NFTs & Digital Asset Protocols",
        "description": "ERC‑721/1155 implementations, metadata standards, onchain creators' platforms, marketplace contracts, royalty engines, and fractionalization tooling."
    },
    {
        "category": "Gaming & Metaverse Applications",
        "description": "Onchain game engines, asset composability layers, play‑to‑earn economies, and metaverse SDKs focused primarily on interactive entertainment."
    },
    {
        "category": "Social & Consumer Applications",
        "description": "Protocols or SDKs for social graphs, content platforms, messaging, ticketing, subscriptions, and other consumer‑oriented experiences."
    },
    {
        "category": "Storage & Data Availability",
        "description": "IPFS pinning tools, Filecoin/Arweave clients, EigenDA or Celestia adapters, and libraries that persist or serve large blobs and proofs."
    },
    {
        "category": "Security Monitoring & Incident Response",
        "description": "Real‑time threat detectors, alerting networks (e.g., Forta), exploit simulators, pause/kill switches, forensic analysis, and post‑mortem tooling."
    }
]

# Create a list of category names for easy access
CATEGORY_NAMES = [cat["category"] for cat in CATEGORIES]
