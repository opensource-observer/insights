CATEGORIES = [
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
