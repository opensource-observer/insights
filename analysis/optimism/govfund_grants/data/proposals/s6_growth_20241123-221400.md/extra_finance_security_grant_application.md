# Ether.fi OP Mainnet LRT Grant

# Basic Information

- **Project Name:** Extra Finance Security Grant Application
- **Project Url:** https://app.charmverse.io/op-grants/extra-finance-security-grant-application-7028250039355781

## Contact Info

- **Email:** Extra Finance
- **Telegram:** Extra Finance is a leveraged yield farming protocol built within the Superchain ecosystem. 
Extra Finance enables users to farm diverse farming pools with customized farming strategies, and it also serves as a lending protocol, allowing users to deposit funds and earn interest.
- **X handle:** ceylon@extrafi.io
- **Discord/Discourse/Community:** https://t.me/phoker_ceylon
- **Demo:** https://twitter.com/extrafi_io
- **Other:** https://app.extrafi.io

# Grant Request

- **OP request Locked:** 4800
- **OP request for User Incentives:** 28850
- **L2 Recipient Address:** 
    - **:** https://github.com/ExtraFi/extra-contracts
- **Please briefly explain how we will be able to confirm that the OP has been spent:** https://docs.extrafi.io/extra_finance/

# Project Details

- **If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A):** 1. Why are they going to succeed? DeFi users require leveraged liquidity providing platforms to execute a wide range of yield strategies. These strategies include market-neutral farming strategy, farming while maintaining exposure to a single asset, etc. ExtraFi is the first well-adopted leveraged yield farming protocol on Optimism, significantly growing the liquidity on Optimism and Superchain, with a TVL exceeding $130M. We've successfully integrated Velodrome AMM, onboarding mainstream LP farming pairs from ecosystem partners such as VELO-USDC of Velodrome, msETH-WETH & msOP-OP & USDC-msUSD of Metronome, USDC-DOLA of Inverse, and USDC-OP, etc. ExtraFi plays a crucial role in boosting liquidity, unleashing the composability of the OP DeFi ecosystem, and enhancing overall capital efficiency. 2. Why is what they are going to build novel or valuable to Optimism? ExtraFi builds unique features that greatly facilitate liquidity providers on Optimism. These features are also cutting-edge in the space: Provide useful tools such as the PnL simulator, which converts financial data to comprehensive graphs, to help users open positions and maximize their return. Provide different build-in farming templates, to help users conveniently implement farming(or open/update position) with corresponding strategies, such as long, short, and neutral. Combined with the PnL simulator, users can directly and visually get the traits and estimate the performances of different farming strategies. Provide features for users to access full control of their positions, including stop-price-range, repay and rebalance. For example, the stop-price-range feature enables users to set prices(minPrice and maxPrice) to automatically close the position once any one of the prices triggers. Provide users with unparalleled access to detailed data, empowering them to make informed decisions when opening positions, such as the daily return, APY breakdown before and after auto-compound, historical prices, average earnings in 30 days, etc. 3. How is this project likely to bring and keep new builders to the Optimism ecosystem Our integration with Velodrome AMM marks enhancement to ExtraFi's range of strategies. After integration, we deliver unique, high-yield strategies that are not just novel within the ecosystem, but also capital-efficient. These strategies are well-positioned to draw in new capital to Optimism, improving liquidity and the usefulness of existing protocols. By providing these customized strategies, ExtraFi is aiding the diversification and growth of the Optimism DeFi landscape, promoting further innovation and user interaction. 4. What are some comparable projects?  What differentiates this one? Alpaca Finance - not on Optimism Tarot - on Optimism (partially similar - not same) Specifically, compared with Tarot, the following are ExtraFi’s unique features: Provide crypto assets directly to perform leveraged farming On Extra Finance, users can directly provide assets as collateral in their wallets instead of getting LP tokens first. The platform will zap the deposit and debt into LP tokens using the best swap route on Velodrome. (No more actions to switch between protocols) PnL Simulator Extra Finance provides a visualized chart with various factors such as price movement, IL, farming duration, etc, enabling users to make informed decisions when opening a position. With the yield farming simulator, users can see the estimated amount they will earn, how changes in price impact their equity value, and the liquidation price based on different position settings. Users can also simulate changes in value for varying leverage settings and borrowed assets. Support Farming with Long/Short or Neutral Viewpoint On Extra Finance, users have control over the exposure of a position. By borrowing different ratios of assets, he/she can hedge exposure or shape the portfolio according to their expectations, and minimize unexpected losses. And Extra Finance also supports one-click farming templates - to simplify the process of setting up farming strategies. These templates allow anyone to start farming like a DeFi expert in no time. Rigorous Farming Calculation APR is capped by emissions, and affected by lending interest, also, there is potential slippage and swap cost in LP zapping. All these are well calculated and listed in 'Summary' before opening a position. Flexible Position Control Once users create a position on Extra Finance, they have the freedom to make adjustments anytime. They can control the exposure by ‘borrow more’ and ‘repay early’, and +/- leverage factors as needed. Extra Finance aims to be a professional yield strategy platform, other than a basic yield aggregator. 5. Service providers: Have you worked on projects similar to this one? We've audited several projects similar to Extra Finance, which are leveraged lending/borrowing farming protocols, including: Notional: "Maximum Returns. Minimum Risk. Lend, borrow, and earn leveraged yield with DeFi's leading fixed rate lending protocol." Derby Finance: "A community-powered yield optimizer that diversifies its exposure over a wide variety of DeFi yield opportunities. They also offer delta-neutral strategies." Blueberry: A protocol that boosts capital efficiency by using multiple other protocols, offering yield vaults. DODO V3: A leveraged market-making solution designed to minimize impermanent loss and improve liquidity management. 6. Will this project be fee-based or free to the end user? ExtraFi provides a variety of farming pools with customized strategies. It also serves as a lending protocol, allowing users to deposit funds and earn interest. This ensures flexibility and accessibility for all users. Our transparent fee structure is designed to support the platform's growth and deliver value to our users. 7. Will this project pay for any portion of the service? Yes, the project will be able to pay for 12% of the service costs. The total requested OP already accounts for the protocol team, covering 12% of the service costs. 8. Will this project be open-source? Yes
- **Do you have a code audit for your project?:** 1. What makes them well-positioned to accomplish your project goals? 2. Is this their first Web3 project? 3. If not, share links to their other projects (e.g., Github repository). 4. Have they worked on anything in the Optimism ecosystem?
- **Please briefly answer all project details questions:** If so, provide an estimate of how many months of funding runway this project has. If there is an active need for financial support, please outline.

# Market Analysis:

- **Please briefly answer all market analysis questions:** Please describe if so and any mitigation measures taken.

# Grant's impact

- **Please briefly answer all grant's impact questions:** No
- **Full list of the project’s labeled contracts:** The codebase consists of approximately 1,827 nSLOC and includes several important components within the contracts directory of the repository: Core Contracts: LendingPool.sol: Implements the main lending and borrowing functionalities, allowing users to supply assets, borrow against collateral, and manage their positions. It handles interest calculations, collateralization ratios, and liquidation processes. VaultFactory.sol: Responsible for deploying new vaults, acting as a factory contract that ensures consistent deployment parameters and manages the registry of all vaults within the protocol. VeloPositionManager.sol: Manages leveraged positions within the protocol, particularly for interactions with the Velodrome platform, facilitating yield farming and liquidity provision strategies. Token Contracts: ExtraInterestBearingToken.sol: Represents interest-bearing tokens issued to users who supply assets to the lending pools. These tokens accrue interest over time, reflecting the user's share in the pool and facilitating the tracking of deposited assets. Reward Contracts: StakingRewards.sol: Manages the staking mechanisms and distributes rewards to users who stake their tokens within the protocol, incentivizing participation and long-term engagement. StakingRewardsDeployer.sol: Facilitates the deployment of new StakingRewards contracts, allowing for scalability and the introduction of new staking programs or reward schemes. Deployment Contracts: ETokenDeployer.sol: Handles the deployment of ExtraInterestBearingToken contracts, ensuring new tokens are correctly initialized and integrated into the lending pools. VaultDeployerSelector.sol: Determines the appropriate deployer when creating new vaults, providing flexibility and modularity in the vault deployment process. Utility Contracts: Payments.sol: Provides functions for handling payments and token transfers within the protocol, ensuring secure and efficient movement of assets. InterestRateUtils.sol: Contains utility functions for calculating interest rates, supporting dynamic adjustments based on market conditions and protocol parameters. ReserveLogic.sol: Implements logic related to reserve management, including updating reserve balances and handling the accrual of interest. ReserveKey.sol: Provides utilities for generating and managing keys associated with reserves, aiding in accurate tracking and referencing within the protocol. Data Structures: DataTypes.sol: Defines custom data types and structures used across the protocol, promoting consistency and clarity in data handling. VaultTypes.sol: Specifies data structures related to vault operations, assisting in the organization and management of vault-specific information. Given the low complexity of the codebase, especially considering our extensive experience with similar leveraged lending and farming protocols, the audit is estimated to take around 10 days.

# Metrics improved by OP incentives

- **Select the metric specified in the mission request:** Sherlock
- **Fill out your metric objective:** https://discord.gg/extra-finance

# Budget and Plan

- **Please briefly answer all budget and plan questions:** Is there another repo somewhere? The one linked has no tests

# Optimism relationship

- **Please briefly answer all Optimism relationship questions:** The tests are in a separate private repo. We can make them available

# External Contributions:

- **Use of Grant-as-a-service provider:** https://defillama.com/protocol/extra-finance#inf
- **Contributions from non-team members:** 0x5A973117Dd273676bf4D14313b80562DC8973ba9

# Compliance and Policies

- **Confirm understanding of clawback and milestone requirements:** Critical
- **Confirmation of understanding grant policies:** Cycle 28
- **KYC information requirement:** Not Completed
- **Certification of legal compliance for token distribution:** Audits application

# Milestones

- **Critical milestones for project execution:**     - {'milestone_type': 'Audit and Special Mission reviewers', 'op_tokens_request': 'Council', 'cycle': 'N/A', 'completed': 'N/A', 'title': 'Valid list of bugs provided', 'source_of_truth': 'Protocol Team / Sherlock official Discord / Sherlock official Twitter', 'op_amount': 'N/A', 'op_deployment_date': 'N/A', 'incentives_due_date': 'N/A'}
