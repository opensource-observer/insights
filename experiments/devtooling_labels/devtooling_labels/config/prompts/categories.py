CATEGORIES = [
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
