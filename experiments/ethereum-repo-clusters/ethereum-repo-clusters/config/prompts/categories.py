CATEGORIES = [
    # DeFi Application Categories
    {
        "category": "Lending & Borrowing Protocols",
        "description": (
            "Lending & Borrowing Protocols include implementations and SDKs for collateralized lending markets, "
            "flash loans, interest rate models, and liquidation mechanisms. These tools handle asset management, "
            "risk scoring, and pool accounting, enabling users to lend or borrow assets in a trust-minimized way."
        )
    },
    {
        "category": "Decentralized Exchanges (DEXs)",
        "description": (
            "DEXs power peer-to-peer asset swaps and liquidity provision. This includes AMM (automated market maker) "
            "frameworks, order book DEXes, routers, aggregators, and liquidity management libraries. They also often "
            "support advanced trading mechanisms like TWAPs, limit orders, and MEV protection."
        )
    },
    {
        "category": "Derivatives & Synthetic Assets",
        "description": (
            "Derivatives & Synthetic Assets frameworks implement perpetual futures, options, and collateralized synthetic "
            "asset systems. These toolkits involve complex pricing oracles, risk engines, margin systems, and settlement layers."
        )
    },
    {
        "category": "Stablecoin Infrastructure",
        "description": (
            "Stablecoin Infrastructure includes minting contracts, collateralization engines, algorithmic stabilization mechanisms, "
            "and off-chain attestation integrations. It also encompasses tools for analyzing backing ratios and peg health."
        )
    },
    {
        "category": "Oracles & Price Feeds",
        "description": (
            "Oracles & Price Feeds provide real-world and cross-chain data into smart contracts. This category covers push-based oracles, "
            "pull-based on-demand queries, cryptoeconomic staking oracles, and off-chain data relayers."
        )
    },
    {
        "category": "Vaults, Yield Strategies & Aggregators",
        "description": (
            "These tools optimize capital across yield-bearing protocols. They include yield routers, auto-compounding vaults, and rebalancers, "
            "as well as SDKs to model risk-return profiles and dynamically allocate capital across farms and lending markets."
        )
    },
    {
        "category": "Asset Management & Portfolio Tooling",
        "description": (
            "Asset Management tooling includes interfaces and libraries for building rebalancing strategies, vault-based funds, on-chain ETFs, "
            "and automated index trackers. They often incorporate fee structures, role-based access, and compliance checks."
        )
    },
    {
        "category": "DeFi Security & Monitoring",
        "description": (
            "Security tools for DeFi include real-time exploit detectors, anomaly detection systems, pause mechanisms, multisig enforcers, "
            "and post-mortem forensic tools. Monitoring dashboards and alerting frameworks fall here as well."
        )
    },
    {
        "category": "Governance & DAO Tooling",
        "description": (
            "Governance & DAO Tooling enables on-chain proposal management, token-weighted voting, off-chain signaling, execution queues, "
            "and guardrails for DeFi governance systems. Includes snapshot integration, timelocks, and delegate management interfaces."
        )
    },
    {
        "category": "Liquidity Bootstrapping & Token Distribution",
        "description": (
            "This includes tools for liquidity mining, airdrops, vesting contracts, bonding curves, and initial token offerings. "
            "They facilitate community-led distribution, price discovery, and progressive decentralization of DeFi protocols."
        )
    },
    {
        "category": "DeFi Analytics & Dashboards",
        "description": (
            "These are SDKs, APIs, and frontends for aggregating on-chain DeFi metrics—TVL, yield, volume, and user activity. "
            "Includes data pipelines, Dune-compatible libraries, subgraphs, and event-based ETL infrastructure tailored to DeFi."
        )
    },
    {
        "category": "Cross-chain DeFi Infrastructure",
        "description": (
            "These tools support multi-chain liquidity routing, cross-chain yield farming, state relays, and synthetic asset issuance. "
            "They abstract away bridging mechanics, offering seamless user and liquidity migration across ecosystems."
        )
    },
    {
        "category": "User Interface & Integration SDKs",
        "description": (
            "SDKs and frontend libraries for integrating DeFi functionality into wallets, dApps, and aggregators. Includes trade UIs, "
            "Zap interfaces, gas estimators, and batch transaction helpers to improve DeFi UX."
        )
    },
    {
        "category": "Simulation & Risk Modeling",
        "description": (
            "Tools that simulate user positions, economic incentives, or protocol upgrades. They model protocol resilience, agent behavior, "
            "market shocks, and contagion scenarios, often using agent-based or Monte Carlo methods for risk-aware design."
        )
    },

    # Developer Tool Categories
    {
        "category": "Language & Compilation Tools",
        "description": (
            "Language & Compilation Tools include compilers, interpreters, language servers, "
            "and syntax utilities for smart-contract development. They translate high-level "
            "source code into EVM bytecode, perform static analysis, and enable features like "
            "symbolic execution, forming the foundation for all higher-level tooling."
        )
    },
    {
        "category": "Core Protocol Interfaces",
        "description": (
            "Core Protocol Interfaces are libraries and SDKs that provide reusable building blocks "
            "for blockchain developers—smart contract libraries, JSON-RPC clients, transaction builders, "
            "wallet and key management, authorization, signature handling, and ABI encoding/decoding. "
            "They can power the core operations of many dApps and services."
        )
    },
    {
        "category": "Development Frameworks",
        "description": (
            "Development Frameworks are opinionated, end-to-end toolchains that scaffold, build, "
            "test, and deploy smart-contract projects. They bundle CLIs, IDE integrations, task "
            "runners, local networks, hot-reloading, and plugin ecosystems to enforce conventions "
            "and automate workflows from project setup through to frontend integration."
        )
    },
    {
        "category": "Deployment & Lifecycle Management",
        "description": (
            "Deployment & Lifecycle Management tools handle contract deployment, upgrades, and "
            "on-chain migrations. They automate predictable CREATE2 strategies, proxy pattern "
            "management, cross-network publishes, and governance hooks, while integrating safety "
            "checks and test-suite validations to maintain contract integrity."
        )
    },
    {
        "category": "Testing & Verification Tools",
        "description": (
            "Testing & Verification Tools provide frameworks for unit testing, property-based fuzzing, "
            "symbolic execution, formal verification, and coverage analysis. They integrate vulnerability "
            "scanners, static analyzers, and coverage reporters to identify edge-case failures and ensure "
            "on-chain correctness."
        )
    },
    {
        "category": "Developer Experience Tools",
        "description": (
            "Developer Experience Tools are lightweight plugins and utilities that boost productivity "
            "and enforce code consistency. This category includes editor extensions, linters, formatters, "
            "code generators, documentation generators, and small CLI helpers."
        )
    },
    {
        "category": "Infrastructure & Node Operations",
        "description": (
            "Infrastructure & Node Operations encompass tools for running, coordinating, and scaling "
            "blockchain nodes and peer-to-peer networks. They cover RPC providers, telemetry collectors, "
            "log aggregators, gossip-based messaging layers, peer discovery and connection management, "
            "and automation scripts to ensure reliable network participation."
        )
    },
    {
        "category": "Data Indexing & Analytics",
        "description": (
            "Data Indexing & Analytics tools ingest, process, and visualize on-chain data. They provide "
            "GraphQL and REST APIs over processed datasets, real-time event streaming, and libraries or "
            "dashboards for analyzing blockchain metrics."
        )
    },
    {
        "category": "Interoperability & Cross-chain",
        "description": (
            "Interoperability & Cross-chain covers bridging frameworks, cross-chain messaging protocols, "
            "and Superchain interoperability tooling. These libraries enable seamless asset transfers, "
            "state proofs, and communication across multiple networks."
        )
    },
    {
        "category": "Cryptography & Primitives",
        "description": (
            "Cryptography & Primitives includes low-level cryptographic libraries and building blocks—"
            "hash functions, signature schemes, Merkle trees, zero-knowledge proof primitives, and "
            "encryption utilities—optimized for security and performance."
        )
    },
    {
        "category": "Application-Specific & Niche Tools",
        "description": (
            "Application-Specific & Niche Tools are libraries and SDKs tailored to very narrow use cases "
            "(e.g., DeFi adapters, NFT marketplaces, governance dashboards). They serve specific projects "
            "but do not have broad applicability or reusability across the ecosystem."
        )
    },
    {
        "category": "Others",
        "description": (
            "Others is a catch-all for repositories with limited usage or insufficient information—"
            "empty projects, single-file utilities, or items that cannot be reasonably categorized."
        )
    }
]

# Create a list of category names for easy access
CATEGORY_NAMES = [cat["category"] for cat in CATEGORIES]
