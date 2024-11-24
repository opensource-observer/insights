# Ether.fi OP Mainnet LRT Grant

# Basic Information

- **Project Name:** Resolv Labs Security Grant Application
- **Project Url:** https://app.charmverse.io/op-grants/resolv-labs-security-grant-application-5072691667085958

## Contact Info

- **Email:** Resolv Labs
- **Telegram:** Resolv is a protocol maintaining USR, a stablecoin natively backed by Ether (ETH) and pegged to the US Dollar.
- **X handle:** resolv@resolv.im
- **Discord/Discourse/Community:** @Resolv_Community
- **Demo:** https://x.com/ResolvLabs
- **Other:** https://resolv.xyz/

# Grant Request

- **OP request Locked:** 13500
- **OP request for User Incentives:** 31500
- **L2 Recipient Address:** 
    - **:** https://github.com/resolv-im
- **Please briefly explain how we will be able to confirm that the OP has been spent:** https://app.resolv.xyz/

# Project Details

- **If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A):** 1. Why are they going to succeed? Resolv Labs is set for success with its innovative $USR stablecoin, which employs a delta-neutral strategy to protect against market volatility. This design, combined with the founders' extensive fintech and software engineering experience, positions them to effectively meet user needs in the Optimism ecosystem. Since the beta launch 4 months ago TVL has grown to 16m with key integrations and partnerships being completed with companies such as Binance, Deribit, and Hyperliquid. Resolv is trusted by investors such as Delphi Labs, No Limit, Daedalus, Tulipa Capital, Stake DAO and others. 2. Why is what they are going to build novel or valuable to Optimism? Considering the size of the stablecoin market (hundreds of billions $) and Optimism's strong growth potential, an advanced Resolv stablecoin could drive significant user growth and adoption on the chain. 3. How is this project likely to bring and keep new builders to the Optimism ecosystem? By providing a reliable and resilient stablecoin, Resolv Labs will attract new builders seeking dependable financial instruments. The RLP allows developers to implement high-yield strategies without excessive risk, improving engagement within the Optimism community. 4. What are some comparable projects? What differentiates this one? Comparable projects include DAI and USDC, which provide stability but lack advanced risk management. Resolv Labs stands out by using a delta-neutral strategy backed by RLP, allowing $USR to maintain its peg more effectively during market fluctuations. In comparison to other delta-neutral stablecoins - the $USR stablecoin offers a mechanism that enhances stability through a self-balanced protective Resolv Liquidity Pool (RLP). This stability is crucial for users and developers, increasing liquidity and utility within the Optimism DeFi landscape alongside the whole DeFi ecosystem. 5. Service providers: Have you worked on projects similar to this one? Sherlock has audited several projects similar to Resolv, which is a protocol maintaining USR, a stablecoin natively backed by Ether (ETH) and pegged to the US Dollar. These projects include: MakerDAO, which operates the DAI stablecoin, a CDP (collateralized-debt-position) stablecoin backed by various assets. UXD Protocol, a fully collateralized decentralized stablecoin backed by delta-neutral positions using derivatives. TapiocaDAO, offering an Omnichain Money Market and Unstoppable OmniDollar StableCoin, based on LayerZeroV2. Volta, an overcollateralized stablecoin protocol. Unitas Protocol, which creates stablecoins for emerging market currencies. Flat Money, a protocol that allows people to deposit Rocket Pool ETH (rETH) and mint UNIT, a decentralized delta-neutral flatcoin designed to outpace inflation. 6. Will this project be fee-based or free to the end user? At the moment and for the near future there are no plans to take any fees. In a more distant future it is likely that fees are going to be taken from the yield of the whole protocol. 7. Will this project be open-source? Yes, Resolv Labs aims for all smart contracts to be open-source, promoting transparency and trust within the Optimism ecosystem.
- **Do you have a code audit for your project?:** 1. What makes them well-positioned to accomplish your project goals? 2. Is this their first Web3 project? 3. If not, share links to their other projects (e.g., Github repository). 4. Have they worked on anything in the Optimism ecosystem?
- **Please briefly answer all project details questions:** If so, provide an estimate of how many months of funding runway this project has. If there is an active need for financial support, please outline.

# Market Analysis:

- **Please briefly answer all market analysis questions:** Please describe if so and any mitigation measures taken.

# Grant's impact

- **Please briefly answer all grant's impact questions:** No.
- **Full list of the project’s labeled contracts:** The codebase consists of approximately 2,008 nSLOC and includes several important contracts within the contracts directory. Key contracts include: StUSR.sol: Implements the USR stablecoin, handling minting, burning, and rebasing functionalities to maintain the peg to the US Dollar. It likely extends from ERC20RebasingUpgradeable.sol to enable rebasing features. Treasury.sol: Manages the protocol's treasury, handling the collateralization of USR with Ether (ETH). It oversees deposits, withdrawals, and interacts with external connectors to optimize asset management. AaveV3TreasuryConnector.sol: Integrates with Aave V3 to utilize the protocol's lending and borrowing functionalities, enabling the treasury to earn yield on deposited Ether and enhance capital efficiency. LidoTreasuryConnector.sol: Connects the treasury to Lido, allowing the protocol to stake Ether and receive staking rewards, further backing USR with yield-generating assets. ERC20RebasingUpgradeable.sol and ERC20RebasingPermitUpgradeable.sol: Provide base functionalities for rebasing tokens, allowing USR to adjust its total supply to maintain its peg, and supporting permit functionality for gasless approvals. WstUSR.sol: A wrapped, non-rebasing version of USR, enabling compatibility with protocols that do not support rebasing tokens while still representing ownership of USR. RewardDistributor.sol: Manages the distribution of rewards to USR holders, potentially from yield generated by the treasury's activities with Aave, Lido, or other integrated protocols. AddressesWhitelist.sol: Implements access control by maintaining a whitelist of addresses allowed to interact with certain protocol functions, enhancing security and compliance. ExternalRequestsManager.sol, ExternalRequestsManagerBetaV1.sol, and LPExternalRequestsManager.sol: Handle external requests and interactions with other contracts or protocols, managing cross-contract communication and ensuring proper execution flow, especially for liquidity providers. SimpleToken.sol: A basic ERC-20 token contract that may be used for testing, utilities, or representing auxiliary tokens within the protocol. Given the medium complexity of the codebase and our extensive experience with similar stablecoin protocols, the audit is estimated to take around 12 days.

# Metrics improved by OP incentives

- **Select the metric specified in the mission request:** Sherlock
- **Fill out your metric objective:** https://discord.com/invite/HwPhyC4hZt

# Budget and Plan

- **Please briefly answer all budget and plan questions:** Is there a second repo? The public one has no tests suggesting it's not ready for an audit or there's another repo somewhere

# Optimism relationship

- **Please briefly answer all Optimism relationship questions:** Hey, Can you reduce the total OP requested amount? Currently it's a bit too high

# External Contributions:

- **Use of Grant-as-a-service provider:** N/A
- **Contributions from non-team members:** 0x5A973117Dd273676bf4D14313b80562DC8973ba9

# Compliance and Policies

- **Confirm understanding of clawback and milestone requirements:** Critical
- **Confirmation of understanding grant policies:** Cycle 29
- **KYC information requirement:** Not Completed
- **Certification of legal compliance for token distribution:** Audits application

# Milestones

- **Critical milestones for project execution:**     - {'milestone_type': 'Audit and Special Mission reviewers', 'op_tokens_request': 'Council', 'cycle': 'N/A', 'completed': 'N/A', 'title': 'Valid list of bugs provided', 'source_of_truth': 'Protocol Team / Sherlock official Discord / Sherlock official Twitter', 'op_amount': 'N/A', 'op_deployment_date': 'N/A', 'incentives_due_date': 'N/A'}
